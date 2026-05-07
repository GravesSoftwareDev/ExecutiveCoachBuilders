"""
Shared helpers for CRM views (list/detail, chat, drafts).

Implementation details for ``leads.views`` — import from ``leads.helpers`` when
needed outside the view package (e.g. dashboard stats).
"""

from __future__ import annotations

from datetime import timedelta

from django.db.models import Count, Max, Prefetch, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from leads.models import Lead, LeadChatSession, LeadMessage


MAX_TITLE_LEN = 120



def is_htmx(request: HttpRequest) -> bool:
    return request.headers.get('HX-Request') == 'true'


def truncate_title(text: str, limit: int = MAX_TITLE_LEN) -> str:
    text = (text or '').strip().replace('\n', ' ')
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + '…'


def split_addrs(raw: str) -> list[str]:
    """Flat list of valid-looking addresses from a 'a@x, b@y' string."""
    out: list[str] = []
    for part in (raw or '').replace(';', ',').split(','):
        addr = part.strip()
        if addr and '@' in addr and addr not in out:
            out.append(addr)
    return out


def annotated_leads():
    """Leads annotated with their last timeline activity timestamp."""
    return Lead.objects.annotate(last_activity_at=Max('messages__created_at'))


def lead_stats(user) -> dict:
    day_ago = timezone.now() - timedelta(days=1)
    agg = Lead.objects.aggregate(
        total=Count('id'),
        open=Count('id', filter=~Q(pipeline_stage=Lead.PipelineStage.CLOSED)),
        hot=Count('id', filter=Q(is_hot=True)),
        mine=Count('id', filter=Q(assigned_to=user) & ~Q(pipeline_stage=Lead.PipelineStage.CLOSED)),
        new_today=Count('id', filter=Q(created_at__gte=day_ago)),
    )
    need_draft = Lead.objects.filter(
        messages__status=LeadMessage.Status.DRAFT,
        messages__direction=LeadMessage.Direction.OUT,
    ).distinct().count()
    agg['need_draft'] = need_draft
    return agg


def chat_sessions_for(lead: Lead) -> list[LeadChatSession]:
    """All sessions for a lead, newest activity last (so the current session
    renders at the bottom of the chat log)."""
    return list(
        lead.chat_sessions
        .prefetch_related(
            Prefetch(
                'messages',
                queryset=LeadMessage.objects.select_related('actor').order_by('created_at'),
                to_attr='ordered_messages',
            )
        )
        .order_by('last_activity_at')
    )


def chat_context(lead: Lead, request: HttpRequest) -> dict:
    sessions = chat_sessions_for(lead)
    starting_fresh = bool(request.session.get(f'chat_new_session:{lead.pk}'))
    active_id = request.session.get(f'chat_active_session:{lead.pk}')

    if starting_fresh or not sessions:
        current = None
    elif active_id is not None:
        current = next((s for s in sessions if s.pk == active_id), sessions[-1])
    else:
        current = sessions[-1]

    past = [s for s in reversed(sessions) if current is None or s.pk != current.pk]

    return {
        'lead': lead,
        'current_session': current,
        'chat_sessions_past': past,
        'starting_fresh': starting_fresh,
    }


def render_chat_panel(request: HttpRequest, lead: Lead) -> HttpResponse:
    return render(request, 'leads/_chat_panel.html', chat_context(lead, request))


def get_or_create_session(
    request: HttpRequest, lead: Lead, *, first_question: str,
) -> LeadChatSession:
    """Resolve the session to tag the next chat turn with.

    Priority: (1) user explicitly clicked "new" -> always new;
              (2) user resumed a specific past session -> reuse it;
              (3) otherwise -> most recently active session.
    """
    must_new = bool(request.session.pop(f'chat_new_session:{lead.pk}', False))

    if not must_new:
        active_id = request.session.get(f'chat_active_session:{lead.pk}')
        if active_id is not None:
            found = lead.chat_sessions.filter(pk=active_id).first()
            if found is not None:
                return found
        latest = lead.chat_sessions.order_by('-last_activity_at').first()
        if latest is not None:
            return latest

    user = request.user if request.user.is_authenticated else None
    return LeadChatSession.objects.create(
        lead=lead,
        started_by=user,
        title=truncate_title(first_question),
    )
