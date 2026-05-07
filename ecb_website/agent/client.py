"""
Thin LLM client that dispatches to OpenAI or Gemini based on the active
provider. Every outbound call is logged to agent.models.LLMCall for
observability (tokens, latency, success/failure).

Public API:
  is_configured()                                  -> bool
  chat_json_completion(system, user, purpose=...)  -> dict
  chat_text_completion(system, user, purpose=...)  -> str
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from agent import config as agent_config

logger = logging.getLogger(__name__)

GEMINI_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta'


@dataclass
class LLMResult:
    raw: dict[str, Any] = field(default_factory=dict)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    success: bool = True
    error_kind: str = ''


def _provider() -> str:
    return agent_config.get_provider()


def is_configured() -> bool:
    provider = _provider()
    if provider == 'gemini':
        return bool(agent_config.get_gemini_api_key())
    elif provider == 'deepseek':
        return bool(agent_config.get_deepseek_api_key())
    elif provider == 'openrouter':
        return bool(agent_config.get_openrouter_api_key())
    return bool(agent_config.get_openai_api_key())


def _record_call(*, provider: str, model: str, purpose: str,
                 result: LLMResult, latency_ms: int,
                 lead_id: int | None, user_id: int | None) -> None:
    try:
        from agent.models import LLMCall
        LLMCall.objects.create(
            provider=provider,
            model=model,
            purpose=purpose,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=result.total_tokens,
            latency_ms=latency_ms,
            success=result.success,
            error_kind=result.error_kind,
            lead_id=lead_id,
            user_id=user_id,
        )
    except Exception as e:
        logger.warning('Failed to record LLMCall: %s', e)


# ── OpenAI ─────────────────────────────────────────────────────────────────

def _openai_post(payload: dict[str, Any], provider: str) -> LLMResult:
    if provider == 'deepseek':
        api_key = agent_config.get_deepseek_api_key()
        base = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1').rstrip('/')
    elif provider == 'openrouter':
        api_key = agent_config.get_openrouter_api_key()
        base = os.environ.get('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1').rstrip('/')
    else:
        api_key = agent_config.get_openai_api_key()
        base = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1').rstrip('/')

    if not api_key:
        return LLMResult(success=False, error_kind='not_configured')

    url = f'{base}/chat/completions'
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        method='POST',
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        logger.warning('OpenAI request failed: %s', e)
        return LLMResult(success=False, error_kind=e.__class__.__name__)

    usage = raw.get('usage') or {}
    return LLMResult(
        raw=raw,
        prompt_tokens=int(usage.get('prompt_tokens', 0) or 0),
        completion_tokens=int(usage.get('completion_tokens', 0) or 0),
        total_tokens=int(usage.get('total_tokens', 0) or 0),
    )


def _openai_extract_text(raw: dict[str, Any]) -> str:
    try:
        content = raw['choices'][0]['message']['content']
        return content.strip() if isinstance(content, str) else ''
    except (KeyError, IndexError, TypeError) as e:
        logger.warning('Unexpected OpenAI response shape: %s', e)
        return ''


# ── Gemini (generateContent) ───────────────────────────────────────────────

def _gemini_post(model: str, payload: dict[str, Any]) -> LLMResult:
    api_key = agent_config.get_gemini_api_key()
    if not api_key:
        return LLMResult(success=False, error_kind='not_configured')

    url = f'{GEMINI_BASE_URL}/models/{model}:generateContent?key={api_key}'
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        method='POST',
        headers={'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        detail = ''
        if isinstance(e, urllib.error.HTTPError):
            try:
                detail = e.read().decode('utf-8')[:400]
            except Exception:
                pass
        logger.warning('Gemini request failed: %s %s', e, detail)
        return LLMResult(success=False, error_kind=e.__class__.__name__)

    usage = raw.get('usageMetadata') or {}
    return LLMResult(
        raw=raw,
        prompt_tokens=int(usage.get('promptTokenCount', 0) or 0),
        completion_tokens=int(usage.get('candidatesTokenCount', 0) or 0),
        total_tokens=int(usage.get('totalTokenCount', 0) or 0),
    )


def _gemini_extract_text(raw: dict[str, Any]) -> str:
    try:
        parts = raw['candidates'][0]['content']['parts']
        chunks = [p.get('text', '') for p in parts if isinstance(p, dict)]
        return ''.join(chunks).strip()
    except (KeyError, IndexError, TypeError) as e:
        logger.warning('Unexpected Gemini response shape: %s', e)
        return ''


# ── Public dispatch ────────────────────────────────────────────────────────

def _resolve_model(provider: str) -> str:
    if provider == 'openai':
        return agent_config.get_openai_model()
    elif provider == 'deepseek':
        return agent_config.get_deepseek_model()
    elif provider == 'openrouter':
        return agent_config.get_openrouter_model()
    return agent_config.get_gemini_model()


def _do_call(*, json_mode: bool, system: str, user: str, temperature: float,
             purpose: str, lead_id: int | None,
             model_override: str = '',
             user_id: int | None = None) -> LLMResult:
    provider = _provider()
    model = model_override or _resolve_model(provider)
    start = time.monotonic()

    if provider == 'gemini':
        cfg: dict[str, Any] = {'temperature': temperature}
        if json_mode:
            cfg['responseMimeType'] = 'application/json'
        result = _gemini_post(model, {
            'systemInstruction': {'parts': [{'text': system}]},
            'contents': [{'role': 'user', 'parts': [{'text': user}]}],
            'generationConfig': cfg,
        })
    else:
        payload: dict[str, Any] = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user},
            ],
            'temperature': temperature,
        }
        if json_mode:
            payload['response_format'] = {'type': 'json_object'}
        result = _openai_post(payload, provider)

    latency_ms = int((time.monotonic() - start) * 1000)
    _record_call(provider=provider, model=model, purpose=purpose,
                 result=result, latency_ms=latency_ms,
                 lead_id=lead_id, user_id=user_id)
    return result


def chat_json_completion(*, system: str, user: str,
                         purpose: str = 'qa', lead_id: int | None = None,
                         model_override: str = '',
                         user_id: int | None = None) -> dict[str, Any]:
    result = _do_call(json_mode=True, system=system, user=user,
                      temperature=0.3, purpose=purpose, lead_id=lead_id,
                      model_override=model_override, user_id=user_id)
    if not result.success or not result.raw:
        return {}
    text = (_gemini_extract_text(result.raw)
            if _provider() == 'gemini'
            else _openai_extract_text(result.raw))
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning('Non-JSON response in json mode: %s', e)
        return {}


def chat_text_completion(*, system: str, user: str, temperature: float = 0.3,
                         purpose: str = 'qa', lead_id: int | None = None,
                         user_id: int | None = None) -> str:
    result = _do_call(json_mode=False, system=system, user=user,
                      temperature=temperature, purpose=purpose, lead_id=lead_id,
                      user_id=user_id)
    if not result.success or not result.raw:
        return ''
    return (_gemini_extract_text(result.raw)
            if _provider() == 'gemini'
            else _openai_extract_text(result.raw))


# ── Streaming ──────────────────────────────────────────────────────────────

def _openai_stream(payload: dict[str, Any], provider: str):
    """Yield text chunks from OpenAI's streaming chat completions endpoint."""
    if provider == 'deepseek':
        api_key = agent_config.get_deepseek_api_key()
        base = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1').rstrip('/')
    elif provider == 'openrouter':
        api_key = agent_config.get_openrouter_api_key()
        base = os.environ.get('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1').rstrip('/')
    else:
        api_key = agent_config.get_openai_api_key()
        base = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1').rstrip('/')

    if not api_key:
        return
    url = f'{base}/chat/completions'
    req = urllib.request.Request(
        url,
        data=json.dumps({**payload, 'stream': True}).encode('utf-8'),
        method='POST',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for raw_line in resp:
                line = raw_line.decode('utf-8', 'replace').strip()
                if not line.startswith('data:'):
                    continue
                data = line[5:].strip()
                if data == '[DONE]':
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                try:
                    delta = chunk['choices'][0]['delta'].get('content') or ''
                except (KeyError, IndexError, TypeError):
                    delta = ''
                if delta:
                    yield delta
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        logger.warning('OpenAI stream failed: %s', e)


def _gemini_stream(model: str, payload: dict[str, Any]):
    """Yield text chunks from Gemini's streamGenerateContent endpoint."""
    api_key = agent_config.get_gemini_api_key()
    if not api_key:
        return
    url = (
        f'{GEMINI_BASE_URL}/models/{model}:streamGenerateContent'
        f'?alt=sse&key={api_key}'
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        method='POST',
        headers={'Content-Type': 'application/json', 'Accept': 'text/event-stream'},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for raw_line in resp:
                line = raw_line.decode('utf-8', 'replace').strip()
                if not line.startswith('data:'):
                    continue
                data = line[5:].strip()
                if not data:
                    continue
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                try:
                    parts = chunk['candidates'][0]['content']['parts']
                    text = ''.join(
                        p.get('text', '') for p in parts if isinstance(p, dict)
                    )
                except (KeyError, IndexError, TypeError):
                    text = ''
                if text:
                    yield text
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        logger.warning('Gemini stream failed: %s', e)


def chat_text_stream(*, system: str, user: str, temperature: float = 0.3,
                     purpose: str = 'qa', lead_id: int | None = None,
                     user_id: int | None = None):
    """
    Yield plain-text chunks as they arrive from the active provider.

    The final LLMCall row is written once the stream ends. Token counts are
    set to 0 because most streaming endpoints do not return usage mid-stream;
    latency is still measured.
    """
    provider = _provider()
    model = _resolve_model(provider)
    start = time.monotonic()
    streamed: list[str] = []
    success = False
    error_kind = ''

    try:
        if provider == 'gemini':
            chunks = _gemini_stream(model, {
                'systemInstruction': {'parts': [{'text': system}]},
                'contents': [{'role': 'user', 'parts': [{'text': user}]}],
                'generationConfig': {'temperature': temperature},
            })
        else:
            chunks = _openai_stream({
                'model': model,
                'messages': [
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': user},
                ],
                'temperature': temperature,
            }, provider)
        for piece in chunks:
            streamed.append(piece)
            yield piece
        success = bool(streamed)
        if not success:
            error_kind = 'empty_stream'
    except Exception as e:
        error_kind = e.__class__.__name__
        logger.warning('Streaming call failed: %s', e)
    finally:
        latency_ms = int((time.monotonic() - start) * 1000)
        _record_call(
            provider=provider, model=model, purpose=purpose,
            result=LLMResult(success=success, error_kind=error_kind),
            latency_ms=latency_ms, lead_id=lead_id, user_id=user_id,
        )
