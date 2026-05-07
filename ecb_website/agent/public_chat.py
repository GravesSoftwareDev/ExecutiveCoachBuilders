"""
Public-site visitor chat (no Lead context).

Uses the same LLM stack as the rest of the agent; purpose is logged as ``website_chat``.
"""

from __future__ import annotations

from agent.client import chat_text_completion, is_configured

SYSTEM_PROMPT = """\
You are the friendly website assistant for Executive Coach Builders (ECB), a U.S. \
manufacturer of luxury executive motorcoaches, Sprinter-based limousines and shuttles, \
and related vehicles. You speak to potential buyers browsing the public website.

Rules:
- Be concise (usually 2–5 sentences). Plain text only; no markdown headings.
- You are not a sales rep on the phone: do not invent specific prices, delivery dates, \
or financing terms. If asked for a firm quote, say a team member will follow up and \
point them to the contact form or phone.
- Describe ECB in general terms: craftsmanship since 1976, custom builds, multi-vehicle programs, \
and that details vary by model and configuration.
- If the question is not about ECB, vehicles, or working with the company, politely \
redirect to how ECB can help with coaches or limousines.
- Never claim access to private customer data or internal systems.
- End with a soft next step when appropriate (e.g. visit Contact, browse Vehicles, \
or call the published number).
""".strip()


def answer_public_question(
    user_message: str,
    history: list[dict],
    *,
    max_history_turns: int = 6,
) -> str:
    """Return assistant reply text, or empty string if LLM is unavailable."""
    if not is_configured():
        return ''
    msg = (user_message or '').strip()[:2000]
    if not msg:
        return ''

    lines: list[str] = []
    for turn in history[-max_history_turns:]:
        role = turn.get('role')
        content = (turn.get('content') or '')[:1500]
        if not content:
            continue
        if role == 'user':
            lines.append(f'Visitor: {content}')
        elif role == 'assistant':
            lines.append(f'Assistant: {content}')

    block = '\n'.join(lines)
    if block:
        user_blob = f'Conversation so far:\n{block}\n\nVisitor message:\n{msg}'
    else:
        user_blob = f'Visitor message:\n{msg}'

    text = chat_text_completion(
        system=SYSTEM_PROMPT,
        user=user_blob,
        temperature=0.35,
        purpose='website_chat',
        lead_id=None,
        user_id=None,
    )
    return (text or '').strip()
