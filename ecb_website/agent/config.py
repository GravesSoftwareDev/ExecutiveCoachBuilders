"""
Resolve LLM runtime config with DB > env > default precedence.

Safe to import early: DB lookups are wrapped, so callers work even before
migrations run (e.g. during `manage.py check`).
"""

from __future__ import annotations

import os

OPENAI_DEFAULT_MODEL = 'gpt-4o-mini'
GEMINI_DEFAULT_MODEL = 'gemini-2.0-flash'
DEEPSEEK_DEFAULT_MODEL = 'deepseek-chat'
OPENROUTER_DEFAULT_MODEL = 'anthropic/claude-3.5-sonnet'

# Cheap models used for high-volume classification (triage) tasks. These stay
# cheap regardless of the premium model selected for enrichment.
OPENAI_DEFAULT_TRIAGE_MODEL = 'gpt-4o-mini'
GEMINI_DEFAULT_TRIAGE_MODEL = 'gemini-2.5-flash-lite'
DEEPSEEK_DEFAULT_TRIAGE_MODEL = 'deepseek-chat'
OPENROUTER_DEFAULT_TRIAGE_MODEL = 'meta-llama/llama-3.1-8b-instruct'


def _db_settings():
    """Return the AgentSettings singleton, or None if DB isn't ready."""
    try:
        from agent.models import AgentSettings
        return AgentSettings.objects.filter(pk=1).first()
    except Exception:
        return None


def get_provider() -> str:
    row = _db_settings()
    if row and row.llm_provider:
        return row.llm_provider.strip().lower()
    return (os.environ.get('LLM_PROVIDER', 'openai') or 'openai').strip().lower()


def get_openai_api_key() -> str:
    row = _db_settings()
    if row and row.openai_api_key:
        return row.openai_api_key
    return os.environ.get('OPENAI_API_KEY', '').strip()


def get_gemini_api_key() -> str:
    row = _db_settings()
    if row and row.gemini_api_key:
        return row.gemini_api_key
    return os.environ.get('GEMINI_API_KEY', '').strip()


def get_deepseek_api_key() -> str:
    row = _db_settings()
    if row and row.deepseek_api_key:
        return row.deepseek_api_key
    return os.environ.get('DEEPSEEK_API_KEY', '').strip()


def get_openrouter_api_key() -> str:
    row = _db_settings()
    if row and row.openrouter_api_key:
        return row.openrouter_api_key
    return os.environ.get('OPENROUTER_API_KEY', '').strip()


def get_openai_model() -> str:
    row = _db_settings()
    if row and row.openai_model:
        return row.openai_model
    return os.environ.get('OPENAI_MODEL', OPENAI_DEFAULT_MODEL)


def get_gemini_model() -> str:
    row = _db_settings()
    if row and row.gemini_model:
        return row.gemini_model
    return os.environ.get('GEMINI_MODEL', GEMINI_DEFAULT_MODEL)


def get_deepseek_model() -> str:
    row = _db_settings()
    if row and row.deepseek_model:
        return row.deepseek_model
    return os.environ.get('DEEPSEEK_MODEL', DEEPSEEK_DEFAULT_MODEL)


def get_openrouter_model() -> str:
    row = _db_settings()
    if row and row.openrouter_model:
        return row.openrouter_model
    return os.environ.get('OPENROUTER_MODEL', OPENROUTER_DEFAULT_MODEL)


def get_triage_model() -> str:
    """Cheap classifier model. Env override > hardcoded cheap default."""
    provider = get_provider()
    if provider == 'gemini':
        return os.environ.get('GEMINI_TRIAGE_MODEL', GEMINI_DEFAULT_TRIAGE_MODEL)
    elif provider == 'deepseek':
        return os.environ.get('DEEPSEEK_TRIAGE_MODEL', DEEPSEEK_DEFAULT_TRIAGE_MODEL)
    elif provider == 'openrouter':
        return os.environ.get('OPENROUTER_TRIAGE_MODEL', OPENROUTER_DEFAULT_TRIAGE_MODEL)
    return os.environ.get('OPENAI_TRIAGE_MODEL', OPENAI_DEFAULT_TRIAGE_MODEL)


def mask_key(key: str) -> str:
    """Display helper: 'sk-abc...xyz' without leaking the full key."""
    if not key:
        return ''
    if len(key) <= 8:
        return '•' * len(key)
    return f'{key[:4]}…{key[-4:]}'
