from __future__ import annotations

import json
import re

from agent.client import chat_json_completion, chat_text_completion, is_configured


_SYSTEM = """You are an editorial assistant for Executive Coach Builders.
Return one JSON object only with keys: title, summary, body.
The body should be clean HTML suitable for a rich text editor. Use paragraphs,
h2/h3 headings, lists, bold/italic sparingly, and no scripts/styles/iframes.
Tone: confident, warm, specific to custom executive motorcoaches and luxury
vehicle builds. Do not invent exact prices, delivery dates, or guarantees."""


def generate_article_draft(*, prompt: str, user_id: int) -> tuple[dict[str, str] | None, str | None]:
    if not is_configured():
        return None, 'AI is not configured. Open Portal -> AI and add a provider key.'

    user = f'Draft a public news/blog article from this brief:\n\n{prompt.strip()}'
    data = chat_json_completion(
        system=_SYSTEM,
        user=user,
        purpose='blog_draft',
        user_id=user_id,
    )
    if not data:
        raw = chat_text_completion(
            system=_SYSTEM + '\nReturn valid JSON only.',
            user=user,
            temperature=0.35,
            purpose='blog_draft',
            user_id=user_id,
        )
        data = _extract_json(raw)

    if not isinstance(data, dict):
        return None, 'The model did not return a usable draft. Try a more specific prompt.'

    return {
        'title': str(data.get('title') or '').strip(),
        'summary': str(data.get('summary') or '').strip(),
        'body': str(data.get('body') or '').strip(),
    }, None


def _extract_json(text: str) -> dict | None:
    text = (text or '').strip()
    if not text:
        return None
    fenced = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    try:
        out = json.loads(text)
        return out if isinstance(out, dict) else None
    except json.JSONDecodeError:
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end > start:
            try:
                out = json.loads(text[start : end + 1])
                return out if isinstance(out, dict) else None
            except json.JSONDecodeError:
                return None
    return None
