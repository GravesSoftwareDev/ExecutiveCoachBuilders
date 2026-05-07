"""
Per-user daily LLM call budget.

Why: a single junk/looping frontend call can burn the whole team's budget.
Admins set `AgentSettings.daily_llm_calls_per_user` in the Settings page;
0 means unlimited. Staff users bypass the limit so admins can still
diagnose outages.

The counter is derived — we just count `LLMCall` rows with
`user_id == request.user.id AND created_at >= today_utc_start`. No extra
counter table, no cache invalidation pain.

Call sites should:
  1. Call `check_user_quota(user)` BEFORE `llm_client.chat_*`.
  2. If denied, surface `QuotaStatus.message` to the user and bail.

Callers that are *not* user-initiated (background enrichment, daily
reports, email triage poller) should pass `user=None` and skip the
check entirely.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Optional


@dataclass(frozen=True)
class QuotaStatus:
    allowed: bool
    limit: int          # 0 means unlimited
    used: int
    remaining: int      # -1 when unlimited
    message: str = ''   # non-empty when allowed is False


def _today_start_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime.combine(now.date(), time.min, tzinfo=timezone.utc)


def _resolve_limit() -> int:
    from agent.models import AgentSettings
    return int(AgentSettings.load().daily_llm_calls_per_user or 0)


def _count_today(user_id: int) -> int:
    from agent.models import LLMCall
    return LLMCall.objects.filter(
        user_id=user_id,
        created_at__gte=_today_start_utc(),
    ).count()


def check_user_quota(user) -> QuotaStatus:
    """Return whether `user` may make one more LLM call today."""
    if user is None or not getattr(user, 'is_authenticated', False):
        # Anonymous / system calls are not per-user-rate-limited here.
        return QuotaStatus(allowed=True, limit=0, used=0, remaining=-1)

    if getattr(user, 'is_staff', False):
        return QuotaStatus(allowed=True, limit=0, used=0, remaining=-1)

    limit = _resolve_limit()
    if limit <= 0:
        return QuotaStatus(allowed=True, limit=0, used=0, remaining=-1)

    used = _count_today(user.pk)
    remaining = max(limit - used, 0)
    if used >= limit:
        return QuotaStatus(
            allowed=False, limit=limit, used=used, remaining=0,
            message=(
                f'Daily AI quota exceeded: {used}/{limit} calls used today. '
                'Try again tomorrow or ask an admin to raise the limit in Settings.'
            ),
        )
    return QuotaStatus(allowed=True, limit=limit, used=used, remaining=remaining)


def user_quota_snapshot(user) -> QuotaStatus:
    """Read-only variant for templates/dashboards (never reports denied)."""
    s = check_user_quota(user)
    if not s.allowed:
        # Preserve the numbers but don't label as "denied" for a status panel.
        return QuotaStatus(
            allowed=True, limit=s.limit, used=s.used, remaining=s.remaining,
        )
    return s
