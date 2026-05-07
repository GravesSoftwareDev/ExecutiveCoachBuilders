"""Route ParsedEmail to leads by thread, sender, or internal-domain heuristics."""

from __future__ import annotations

from dataclasses import dataclass

from leads.models import Lead, LeadMessage

from .parser import ParsedEmail


@dataclass
class MatchResult:
    kind: str
    lead: Lead | None = None
    replied_to: LeadMessage | None = None


def _clean_mid(raw: str) -> str:
    return (raw or '').strip().strip('<>')


def find_by_in_reply_to(msg: ParsedEmail) -> MatchResult | None:
    candidates: list[str] = []
    if msg.in_reply_to:
        candidates.append(msg.in_reply_to)
    if msg.references:
        candidates.extend(msg.references.split())
    seen: set[str] = set()
    for raw in candidates:
        mid = _clean_mid(raw)
        if not mid or mid in seen:
            continue
        seen.add(mid)
        found = (
            LeadMessage.objects
            .filter(message_id__iexact=f'<{mid}>')
            .first()
            or LeadMessage.objects
            .filter(message_id__iexact=mid)
            .first()
        )
        if found and found.lead_id:
            return MatchResult(kind='thread_match', lead=found.lead, replied_to=found)
    return None


def find_by_sender(msg: ParsedEmail) -> MatchResult | None:
    if not msg.from_email:
        return None
    lead = (
        Lead.objects
        .filter(email__iexact=msg.from_email)
        .order_by('-created_at')
        .first()
    )
    if lead is not None:
        return MatchResult(kind='sender_match', lead=lead)
    return None


def is_internal_reply(msg: ParsedEmail, *, internal_domains: list[str]) -> bool:
    if not msg.from_email or '@' not in msg.from_email:
        return False
    domain = msg.from_email.rsplit('@', 1)[1].lower()
    return any(domain == d or domain.endswith('.' + d) for d in internal_domains)


def match(msg: ParsedEmail, *, internal_domains: list[str]) -> MatchResult:
    result = find_by_in_reply_to(msg)
    if result is not None:
        if is_internal_reply(msg, internal_domains=internal_domains):
            result.kind = 'internal_reply'
        return result

    if is_internal_reply(msg, internal_domains=internal_domains):
        return MatchResult(kind='internal_reply')

    result = find_by_sender(msg)
    if result is not None:
        return result

    return MatchResult(kind='unknown')
