"""
Interactive Q&A on a Lead.

The sales rep opens a lead page and asks natural-language questions about the
customer ("what's their budget?", "draft a follow-up for pricing"). We feed
the LLM three layers of context:

  - long-term memory: lead.ai_structured (summary, hot assessment, tags)
  - short-term context: most recent non-chat messages on the timeline
  - conversation memory: recent Q&A turns on this lead

By default only the last MAX_CONTEXT_MESSAGES non-chat messages are sent.
Callers can pass full_history=True to include every timeline message; use
sparingly because it costs tokens and dilutes attention.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from .client import chat_text_completion, chat_text_stream, is_configured

if TYPE_CHECKING:
    from leads.models import Lead, LeadMessage

MAX_CONTEXT_MESSAGES = 10
MAX_CHAT_TURNS = 6

SYSTEM_PROMPT = """\
You are an internal sales assistant helping an Executive Coach Builders sales
rep understand and respond to a single lead. You will be given a JSON blob
with the lead profile, the AI-generated summary (if any), recent messages on
the timeline, and the most recent Q&A turns.

Rules:
- Ground every claim in the provided context. If the answer is not in the
  context, say so plainly ("I don't have that information from the record").
- Recent messages are more authoritative than the ai_structured summary when
  they conflict.
- Be concise. Default to 1-4 sentences unless the user explicitly asks for a
  draft reply, in which case produce a clean email body only (no signature
  placeholder, no subject line unless asked).
- Do not invent prices, delivery dates, or customer statements.
- Respond in plain text; no markdown headings, no JSON.
""".strip()


def _lead_profile(lead: 'Lead') -> dict[str, Any]:
    return {
        'id': lead.pk,
        'first_name': lead.first_name,
        'last_name': lead.last_name,
        'email': lead.email,
        'phone_number': lead.phone_number or '',
        'company': lead.company or '',
        'budget': lead.budget,
        'interest': lead.interest,
        'passenger_count': lead.passenger_count or '',
        'timeline': lead.timeline or '',
        'use_case': lead.use_case or '',
        'source': lead.source or '',
        'source_url': lead.source_url or '',
        'initial_message': lead.message or '',
        'pipeline_stage': lead.pipeline_stage,
        'is_hot': lead.is_hot,
        'hot_reason': lead.hot_reason or '',
    }


def _serialize_message(m: 'LeadMessage') -> dict[str, Any]:
    return {
        'direction': m.direction,
        'channel': m.channel,
        'status': m.status,
        'subject': m.subject,
        'body': m.body,
        'is_ai_generated': m.is_ai_generated,
        'created_at': m.created_at.isoformat(),
    }


def _recent_non_chat(lead: 'Lead', *, limit: int | None) -> list[dict[str, Any]]:
    from leads.models import LeadMessage
    qs = lead.messages.exclude(channel=LeadMessage.Channel.CHAT).order_by('-created_at')
    if limit is not None:
        qs = qs[:limit]
    rows = list(qs)
    rows.reverse()
    return [_serialize_message(m) for m in rows]


def _recent_chat_turns(lead: 'Lead', limit: int = MAX_CHAT_TURNS) -> list[dict[str, str]]:
    from leads.models import LeadMessage
    qs = lead.messages.filter(channel=LeadMessage.Channel.CHAT).order_by('-created_at')[:limit]
    rows = list(qs)
    rows.reverse()
    turns = []
    for m in rows:
        role = 'assistant' if m.is_ai_generated else 'user'
        turns.append({'role': role, 'content': m.body})
    return turns


def build_context(lead: 'Lead', *, full_history: bool = False) -> dict[str, Any]:
    return {
        'lead': _lead_profile(lead),
        'ai_structured': lead.ai_structured or {},
        'recent_messages': _recent_non_chat(
            lead,
            limit=None if full_history else MAX_CONTEXT_MESSAGES,
        ),
        'prior_qa': _recent_chat_turns(lead),
    }


def answer_question(
    lead: 'Lead', question: str, *, full_history: bool = False,
    user_id: int | None = None,
) -> str:
    """Return the assistant's plain-text answer, or '' when the LLM is off."""
    if not is_configured() or not question.strip():
        return ''

    ctx = build_context(lead, full_history=full_history)
    user_payload = json.dumps(
        {'context': ctx, 'question': question.strip()},
        ensure_ascii=False,
    )
    return chat_text_completion(
        system=SYSTEM_PROMPT, user=user_payload,
        purpose='qa', lead_id=lead.pk, user_id=user_id,
    )


def answer_question_stream(
    lead: 'Lead', question: str, *, full_history: bool = False,
    user_id: int | None = None,
):
    """
    Yield plain-text chunks of the assistant's answer as they arrive.

    Yields an empty iterator when the LLM is unconfigured, so the caller can
    always treat the result as a (possibly empty) stream.
    """
    if not is_configured() or not question.strip():
        return
    ctx = build_context(lead, full_history=full_history)
    user_payload = json.dumps(
        {'context': ctx, 'question': question.strip()},
        ensure_ascii=False,
    )
    yield from chat_text_stream(
        system=SYSTEM_PROMPT, user=user_payload,
        purpose='qa', lead_id=lead.pk, user_id=user_id,
    )
