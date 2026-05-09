from __future__ import annotations

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Max, Q
from django.forms import model_to_dict
from django.http import HttpRequest, HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import DetailView, ListView

from account.decorators import staff_required
from agent.client import is_configured
from agent.qa import answer_question, answer_question_stream
from agent.quota import check_user_quota
from emailing import config as email_config
from emailing.sender import SendFailed, clear_send_error, record_send_failure, send_draft
from .forms import LeadForm
from .helpers import chat_context, get_or_create_session, is_htmx, render_chat_panel
from .models import Lead, LeadChatSession, LeadMessage


def annotated_leads():
    return Lead.objects.annotate(last_activity_at=Max('messages__created_at'))


def lead_stats(user) -> dict:
    return {
        'total': Lead.objects.count(),
        'open': Lead.objects.exclude(pipeline_stage=Lead.PipelineStage.CLOSED).count(),
        'hot': Lead.objects.filter(is_hot=True).count(),
        'mine': Lead.objects.filter(assigned_to=user).exclude(
            pipeline_stage=Lead.PipelineStage.CLOSED,
        ).count(),
        'need_draft': Lead.objects.filter(
            messages__status=LeadMessage.Status.DRAFT,
            messages__direction=LeadMessage.Direction.OUT,
        ).distinct().count(),
    }


class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = 'leads/lead_list.html'
    context_object_name = 'leads'
    paginate_by = 25

    FILTERS = {
        'all': lambda qs, user: qs,
        'mine': lambda qs, user: qs.filter(assigned_to=user),
        'hot': lambda qs, user: qs.filter(is_hot=True),
        'open': lambda qs, user: qs.exclude(pipeline_stage=Lead.PipelineStage.CLOSED),
    }

    SORTS = {
        'recent': ('-last_activity_at', '-created_at'),
        'hot': ('-is_hot', '-last_activity_at', '-created_at'),
        'newest': ('-created_at',),
        'oldest': ('created_at',),
    }

    def get_queryset(self):
        qs = annotated_leads().select_related('assigned_to')
        key = self.request.GET.get('filter', 'open')
        qs = self.FILTERS.get(key, self.FILTERS['open'])(qs, self.request.user)

        search = (self.request.GET.get('q') or '').strip()
        if search:
            qs = qs.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(company__icontains=search)
            )

        sort = self.request.GET.get('sort', 'hot')
        return qs.order_by(*self.SORTS.get(sort, self.SORTS['hot']))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'active_section': 'leads',
            'stats': lead_stats(self.request.user),
            'current_filter': self.request.GET.get('filter', 'open'),
            'current_sort': self.request.GET.get('sort', 'hot'),
            'search_q': self.request.GET.get('q', ''),
            'sort_options': [
                ('hot', 'Hot first'),
                ('recent', 'Latest activity'),
                ('newest', 'Newest'),
                ('oldest', 'Oldest'),
            ],
        })
        return ctx


class LeadDetailView(LoginRequiredMixin, DetailView):
    model = Lead
    template_name = 'leads/lead_detail.html'
    context_object_name = 'lead'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lead: Lead = self.object
        ctx['active_section'] = 'leads'
        ctx['timeline'] = (
            lead.messages
            .exclude(channel=LeadMessage.Channel.CHAT)
            .select_related('actor')
            .order_by('-created_at')
        )
        ctx['pipeline_choices'] = Lead.PipelineStage.choices
        ctx['reply_in_reply_to'] = (
            lead.messages
            .filter(channel=LeadMessage.Channel.EMAIL)
            .exclude(message_id='')
            .order_by('-created_at')
            .values_list('message_id', flat=True)
            .first()
            or ''
        )
        ctx.update(chat_context(lead, self.request))
        return ctx


@staff_required
def lead_create(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save()
            LeadMessage.objects.create(
                lead=lead,
                direction=LeadMessage.Direction.INTERNAL,
                channel=LeadMessage.Channel.SYSTEM,
                status=LeadMessage.Status.LOGGED,
                subject='Lead created',
                body=f'Manually created by {request.user.get_username()}.',
                actor=request.user,
            )
            if lead.message:
                LeadMessage.objects.create(
                    lead=lead,
                    direction=LeadMessage.Direction.IN,
                    channel=LeadMessage.Channel.FORM,
                    status=LeadMessage.Status.RECEIVED,
                    subject='Manual lead intake',
                    body=lead.message,
                    from_email=lead.email,
                    actor=request.user,
                )
            messages.success(request, 'Lead created.')
            return redirect('leads:lead_detail', pk=lead.pk)
    else:
        form = LeadForm(initial={'source': 'manual_portal'})
    return render(
        request,
        'leads/lead_form.html',
        {'form': form, 'active_section': 'leads', 'action': 'New lead'},
    )


@staff_required
def lead_edit(request: HttpRequest, pk: int) -> HttpResponse:
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            LeadMessage.objects.create(
                lead=lead,
                direction=LeadMessage.Direction.INTERNAL,
                channel=LeadMessage.Channel.SYSTEM,
                status=LeadMessage.Status.LOGGED,
                subject='Lead updated',
                body=f'Edited by {request.user.get_username()}.',
                actor=request.user,
            )
            messages.success(request, 'Lead updated.')
            return redirect('leads:lead_detail', pk=lead.pk)
    else:
        form = LeadForm(instance=lead)
    return render(
        request,
        'leads/lead_form.html',
        {'form': form, 'lead': lead, 'active_section': 'leads', 'action': 'Edit lead'},
    )


@login_required
@require_POST
def claim_lead(request: HttpRequest, pk: int) -> HttpResponse:
    lead = get_object_or_404(Lead, pk=pk)
    lead.assigned_to = request.user
    lead.save(update_fields=['assigned_to', 'updated_at'])
    LeadMessage.objects.create(
        lead=lead,
        direction=LeadMessage.Direction.INTERNAL,
        channel=LeadMessage.Channel.SYSTEM,
        status=LeadMessage.Status.LOGGED,
        subject='Assigned',
        body=f'Claimed by {request.user.get_username()}.',
        actor=request.user,
    )
    messages.success(request, 'Lead assigned to you.')
    return redirect('leads:lead_detail', pk=pk)


@login_required
@require_POST
def set_stage(request: HttpRequest, pk: int) -> HttpResponse:
    lead = get_object_or_404(Lead, pk=pk)
    stage = request.POST.get('stage', '')
    valid = {c[0] for c in Lead.PipelineStage.choices}
    if stage not in valid:
        messages.error(request, 'Invalid stage.')
        return redirect('leads:lead_detail', pk=pk)
    old = lead.pipeline_stage
    if old != stage:
        lead.pipeline_stage = stage
        lead.save(update_fields=['pipeline_stage', 'updated_at'])
        LeadMessage.objects.create(
            lead=lead,
            direction=LeadMessage.Direction.INTERNAL,
            channel=LeadMessage.Channel.SYSTEM,
            status=LeadMessage.Status.LOGGED,
            subject='Stage change',
            body=f'{old} -> {stage}',
            actor=request.user,
        )
    messages.success(request, f'Stage set to {lead.get_pipeline_stage_display()}.')
    return redirect('leads:lead_detail', pk=pk)


@login_required
@require_POST
def add_note(request: HttpRequest, pk: int) -> HttpResponse:
    lead = get_object_or_404(Lead, pk=pk)
    body = (request.POST.get('body') or '').strip()
    if not body:
        messages.error(request, 'Note body is required.')
        return redirect('leads:lead_detail', pk=pk)
    LeadMessage.objects.create(
        lead=lead,
        direction=LeadMessage.Direction.INTERNAL,
        channel=LeadMessage.Channel.NOTE,
        status=LeadMessage.Status.LOGGED,
        subject='Note',
        body=body,
        actor=request.user,
    )
    messages.success(request, 'Note added.')
    return redirect('leads:lead_detail', pk=pk)


@staff_required
@require_POST
def lead_send_email(request: HttpRequest, pk: int) -> HttpResponse:
    """Send email to the lead via configured SMTP; stores outbound on the timeline."""
    lead = get_object_or_404(Lead, pk=pk)
    subject = (request.POST.get('subject') or '').strip()
    body = (request.POST.get('body') or '').strip()
    in_reply_to = (request.POST.get('in_reply_to') or '').strip()
    if not body:
        messages.error(request, 'Message body is required.')
        return redirect('leads:lead_detail', pk=pk)
    if not subject:
        subject = 'Executive Coach Builders'

    smtp_cfg = email_config.get_smtp()
    if not (smtp_cfg.enabled and smtp_cfg.configured):
        messages.error(
            request,
            'SMTP is not enabled or incomplete. Configure the Sales mailbox under Portal Settings → Email.',
        )
        return redirect('leads:lead_detail', pk=pk)

    draft = LeadMessage.objects.create(
        lead=lead,
        direction=LeadMessage.Direction.OUT,
        channel=LeadMessage.Channel.EMAIL,
        status=LeadMessage.Status.DRAFT,
        subject=subject,
        body=body,
        in_reply_to=in_reply_to,
        actor=request.user,
        metadata={'source': 'portal_smtp'},
    )

    try:
        result = send_draft(draft)
    except SendFailed as exc:
        record_send_failure(draft, str(exc))
        messages.error(request, f'Send failed: {exc}')
        return redirect('leads:lead_detail', pk=pk)

    clear_send_error(draft)
    draft.message_id = result.message_id
    draft.from_email = smtp_cfg.from_address
    draft.to_email = lead.email
    draft.status = LeadMessage.Status.SENT
    draft.sent_at = timezone.now()
    draft.actor = request.user
    draft.save(update_fields=[
        'message_id', 'from_email', 'to_email', 'status', 'sent_at', 'actor', 'metadata',
    ])
    messages.success(request, f'Email sent to {lead.email}.')
    return redirect('leads:lead_detail', pk=pk)


@staff_required
def lead_delete(request: HttpRequest, pk: int) -> HttpResponse:
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        label = f'{lead.first_name} {lead.last_name}'
        lead.delete()
        messages.success(request, f'Lead "{label}" has been deleted.')
        return redirect('leads:lead_list')
    return render(
        request,
        'leads/lead_confirm_delete.html',
        {'lead': lead, 'active_section': 'leads'},
    )


def _json_payload(request: HttpRequest) -> dict:
    if request.body:
        try:
            return json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return {}
    return request.POST.dict()


def _lead_payload(lead: Lead) -> dict:
    data = model_to_dict(
        lead,
        fields=[
            'id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'company',
            'budget',
            'interest',
            'passenger_count',
            'timeline',
            'use_case',
            'source',
            'source_url',
            'message',
            'pipeline_stage',
            'priority',
            'is_hot',
            'hot_reason',
            'assigned_to',
        ],
    )
    data.update({
        'interest_label': lead.get_interest_display(),
        'pipeline_stage_label': lead.get_pipeline_stage_display(),
        'priority_label': lead.get_priority_display(),
        'assigned_to_username': lead.assigned_to.get_username() if lead.assigned_to else '',
        'created_at': lead.created_at.isoformat(),
        'updated_at': lead.updated_at.isoformat(),
        'detail_url': reverse('leads:lead_detail', args=[lead.pk]),
    })
    return data


@staff_required
def lead_api_collection(request: HttpRequest) -> JsonResponse:
    if request.method == 'GET':
        qs = Lead.objects.select_related('assigned_to').order_by('-created_at')
        search = (request.GET.get('q') or '').strip()
        if search:
            qs = qs.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(company__icontains=search)
            )
        return JsonResponse({'leads': [_lead_payload(lead) for lead in qs[:100]]})

    if request.method == 'POST':
        form = LeadForm(_json_payload(request))
        if form.is_valid():
            lead = form.save()
            LeadMessage.objects.create(
                lead=lead,
                direction=LeadMessage.Direction.INTERNAL,
                channel=LeadMessage.Channel.SYSTEM,
                status=LeadMessage.Status.LOGGED,
                subject='Lead created',
                body=f'Created via API by {request.user.get_username()}.',
                actor=request.user,
            )
            return JsonResponse({'lead': _lead_payload(lead)}, status=201)
        return JsonResponse({'errors': form.errors}, status=400)

    return JsonResponse({'error': 'Method not allowed.'}, status=405)


@staff_required
def lead_api_detail(request: HttpRequest, pk: int) -> JsonResponse:
    lead = get_object_or_404(Lead, pk=pk)

    if request.method == 'GET':
        return JsonResponse({'lead': _lead_payload(lead)})

    if request.method in {'PUT', 'PATCH'}:
        payload = _json_payload(request)
        data = model_to_dict(lead)
        data.update(payload)
        form = LeadForm(data, instance=lead)
        if form.is_valid():
            lead = form.save()
            LeadMessage.objects.create(
                lead=lead,
                direction=LeadMessage.Direction.INTERNAL,
                channel=LeadMessage.Channel.SYSTEM,
                status=LeadMessage.Status.LOGGED,
                subject='Lead updated',
                body=f'Updated via API by {request.user.get_username()}.',
                actor=request.user,
            )
            return JsonResponse({'lead': _lead_payload(lead)})
        return JsonResponse({'errors': form.errors}, status=400)

    if request.method == 'DELETE':
        lead.delete()
        return JsonResponse({'deleted': True})

    return JsonResponse({'error': 'Method not allowed.'}, status=405)


_AI_NOT_CONFIGURED = (
    'LLM is not configured. Open Portal -> AI, choose a provider, and save the matching API key.'
)
_AI_CALL_FAILED = (
    'AI could not complete this request. Check the provider key, quota, selected model, and network access in Portal -> AI, then try again.'
)


def _fallback_ai_reply() -> str:
    if not is_configured():
        return _AI_NOT_CONFIGURED
    return _AI_CALL_FAILED


@login_required
@require_POST
def ask_ai(request: HttpRequest, pk: int) -> HttpResponse:
    lead = get_object_or_404(Lead, pk=pk)
    question = (request.POST.get('question') or '').strip()
    if not question:
        if is_htmx(request):
            return render_chat_panel(request, lead)
        messages.error(request, 'Please type a question.')
        return redirect(f"{reverse('leads:lead_detail', args=[pk])}#ai-chat")

    quota = check_user_quota(request.user)
    if not quota.allowed:
        messages.error(request, quota.message)
        if is_htmx(request):
            return render_chat_panel(request, lead)
        return redirect(f"{reverse('leads:lead_detail', args=[pk])}#ai-chat")

    full_history = request.POST.get('full_history') == 'on'
    session = get_or_create_session(request, lead, first_question=question)

    LeadMessage.objects.create(
        lead=lead,
        chat_session=session,
        direction=LeadMessage.Direction.INTERNAL,
        channel=LeadMessage.Channel.CHAT,
        status=LeadMessage.Status.LOGGED,
        subject='Question',
        body=question,
        actor=request.user,
        metadata={'full_history': full_history},
    )

    answer = answer_question(
        lead, question, full_history=full_history, user_id=request.user.pk,
    ) or _fallback_ai_reply()

    LeadMessage.objects.create(
        lead=lead,
        chat_session=session,
        direction=LeadMessage.Direction.INTERNAL,
        channel=LeadMessage.Channel.CHAT,
        status=LeadMessage.Status.LOGGED,
        subject='Answer',
        body=answer,
        is_ai_generated=True,
        metadata={'full_history': full_history},
    )
    session.save(update_fields=['last_activity_at'])

    if is_htmx(request):
        return render_chat_panel(request, lead)
    return redirect(f"{reverse('leads:lead_detail', args=[pk])}#ai-chat")


@login_required
@require_POST
def ask_ai_stream(request: HttpRequest, pk: int) -> HttpResponse:
    lead = get_object_or_404(Lead, pk=pk)
    question = (request.POST.get('question') or '').strip()
    if not question:
        return HttpResponse(status=204)

    quota = check_user_quota(request.user)
    if not quota.allowed:
        import json as _json

        def denied_stream():
            yield f'data: {_json.dumps({"error": quota.message})}\n\n'
            yield f'data: {_json.dumps({"done": True, "message_id": None})}\n\n'

        resp = StreamingHttpResponse(denied_stream(), content_type='text/event-stream')
        resp['Cache-Control'] = 'no-cache'
        resp['X-Accel-Buffering'] = 'no'
        return resp

    full_history = request.POST.get('full_history') == 'on'
    session = get_or_create_session(request, lead, first_question=question)
    user_id = request.user.pk

    LeadMessage.objects.create(
        lead=lead,
        chat_session=session,
        direction=LeadMessage.Direction.INTERNAL,
        channel=LeadMessage.Channel.CHAT,
        status=LeadMessage.Status.LOGGED,
        subject='Question',
        body=question,
        actor=request.user,
        metadata={'full_history': full_history},
    )

    def event_stream():
        import json as _json

        collected: list[str] = []
        try:
            for chunk in answer_question_stream(
                lead, question, full_history=full_history, user_id=user_id,
            ):
                collected.append(chunk)
                yield f'data: {_json.dumps({"delta": chunk})}\n\n'
        except Exception as exc:
            yield f'data: {_json.dumps({"error": str(exc)})}\n\n'

        answer = ''.join(collected).strip()
        if not answer:
            answer = _fallback_ai_reply()
            yield f'data: {_json.dumps({"delta": answer})}\n\n'
        msg = LeadMessage.objects.create(
            lead=lead,
            chat_session=session,
            direction=LeadMessage.Direction.INTERNAL,
            channel=LeadMessage.Channel.CHAT,
            status=LeadMessage.Status.LOGGED,
            subject='Answer',
            body=answer,
            is_ai_generated=True,
            metadata={'full_history': full_history, 'streamed': True},
        )
        session.save(update_fields=['last_activity_at'])
        yield f'data: {_json.dumps({"done": True, "message_id": msg.pk})}\n\n'

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@login_required
def chat_panel(request: HttpRequest, pk: int) -> HttpResponse:
    lead = get_object_or_404(Lead, pk=pk)
    return render_chat_panel(request, lead)


@login_required
@require_GET
def task_legacy_redirect(request: HttpRequest, pk: int) -> HttpResponse:
    get_object_or_404(Lead, pk=pk)
    return redirect(f"{reverse('leads:lead_detail', args=[pk])}#ai-chat")


@login_required
@require_POST
def new_chat(request: HttpRequest, pk: int) -> HttpResponse:
    lead = get_object_or_404(Lead, pk=pk)
    request.session[f'chat_new_session:{lead.pk}'] = True
    request.session.pop(f'chat_active_session:{lead.pk}', None)
    if is_htmx(request):
        return render_chat_panel(request, lead)
    return redirect(f"{reverse('leads:lead_detail', args=[pk])}#ai-chat")


@login_required
@require_POST
def resume_chat(request: HttpRequest, lead_pk: int, pk: int) -> HttpResponse:
    lead = get_object_or_404(Lead, pk=lead_pk)
    session = get_object_or_404(LeadChatSession, pk=pk, lead=lead)
    request.session[f'chat_active_session:{lead.pk}'] = session.pk
    request.session.pop(f'chat_new_session:{lead.pk}', None)
    if is_htmx(request):
        return render_chat_panel(request, lead)
    return redirect(f"{reverse('leads:lead_detail', args=[lead_pk])}#ai-chat")


@login_required
@require_POST
def delete_chat_session(request: HttpRequest, lead_pk: int, pk: int) -> HttpResponse:
    lead = get_object_or_404(Lead, pk=lead_pk)
    session = get_object_or_404(LeadChatSession, pk=pk, lead=lead)
    sid = session.pk
    request.session.pop(f'chat_new_session:{lead.pk}', None)
    if request.session.get(f'chat_active_session:{lead.pk}') == sid:
        request.session.pop(f'chat_active_session:{lead.pk}', None)
    session.delete()
    messages.success(request, 'Conversation deleted.')
    if is_htmx(request):
        return render_chat_panel(request, lead)
    return redirect(f"{reverse('leads:lead_detail', args=[lead_pk])}#ai-chat")
