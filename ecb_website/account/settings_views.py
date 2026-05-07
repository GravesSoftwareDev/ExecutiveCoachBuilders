from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from account.decorators import staff_required
from agent import client as llm_client
from agent import config as agent_config
from agent.forms import ProviderForm, QuotaForm
from agent.models import AgentSettings, LLMCall
from emailing import config as email_config
from emailing.adapters.imap import ImapError, fetch_unseen, imap_selftest
from emailing.forms import ImapForm, SmtpForm
from emailing.intake import intake_raw
from emailing.models import EmailSettings
from emailing.sender import SendFailed, send_test_to, smtp_selftest

_VALID_PROVIDERS = {'openai', 'gemini', 'deepseek', 'openrouter'}


def _purpose_label(purpose: str) -> str:
    choices = dict(LLMCall.Purpose.choices)
    if purpose in choices:
        return str(choices[purpose])
    return (purpose or 'unknown').replace('_', ' ').title()


def _settings_context(
    request,
    *,
    provider=None,
    form=None,
    quota_form=None,
    email_tab=None,
    smtp_form=None,
    imap_form=None,
):
    row = AgentSettings.load()
    active = agent_config.get_provider()
    tab = provider or request.GET.get('p') or active
    if tab not in _VALID_PROVIDERS:
        tab = active if active in _VALID_PROVIDERS else 'openai'

    form = form or ProviderForm(provider=tab, settings_row=row)
    quota_form = quota_form or QuotaForm(settings_row=row)

    masked = {
        'openai': agent_config.mask_key(agent_config.get_openai_api_key()),
        'gemini': agent_config.mask_key(agent_config.get_gemini_api_key()),
        'deepseek': agent_config.mask_key(agent_config.get_deepseek_api_key()),
        'openrouter': agent_config.mask_key(agent_config.get_openrouter_api_key()),
    }
    since = timezone.now() - timedelta(days=7)
    recent = LLMCall.objects.filter(created_at__gte=since)
    agg = recent.aggregate(
        total=Count('id'),
        errors=Count('id', filter=Q(success=False)),
        tokens=Sum('total_tokens'),
    )
    by_purpose = [
        {
            'label': _purpose_label(row['purpose'] or ''),
            'calls': row['calls'],
            'tokens': row['tokens'] or 0,
        }
        for row in recent.values('purpose')
        .annotate(calls=Count('id'), tokens=Sum('total_tokens'))
        .order_by('-calls', 'purpose')
    ]

    section = request.GET.get('section') or 'ai'
    if section not in ('ai', 'email'):
        section = 'ai'

    email_row = EmailSettings.load()
    smtp_cfg = email_config.get_smtp()
    imap_cfg = email_config.get_imap()
    etab = email_tab or request.GET.get('e') or 'smtp'
    if etab not in {'smtp', 'imap'}:
        etab = 'smtp'
    if smtp_form is None:
        smtp_form = SmtpForm(settings_row=email_row)
    if imap_form is None:
        imap_form = ImapForm(settings_row=email_row)
    policy_limit = int(row.daily_llm_calls_per_user or 0)

    email_status = {
        'smtp_enabled': smtp_cfg.enabled and smtp_cfg.configured,
        'imap_enabled': imap_cfg.enabled and imap_cfg.configured,
        'smtp_configured': smtp_cfg.configured,
        'imap_configured': imap_cfg.configured,
        'smtp_host': smtp_cfg.host,
        'smtp_port': smtp_cfg.port,
        'smtp_from': smtp_cfg.from_address,
        'smtp_password_masked': email_config.mask_password(smtp_cfg.password),
        'imap_host': imap_cfg.host,
        'imap_port': imap_cfg.port,
        'imap_username': imap_cfg.username,
        'imap_folder': imap_cfg.folder,
        'imap_password_masked': email_config.mask_password(imap_cfg.password),
        'last_poll_at': email_row.last_poll_at,
        'last_poll_status': email_row.last_poll_status,
        'internal_domains': email_config.get_internal_domains(),
    }

    return {
        'active_section': 'settings',
        'settings_section': section,
        'active': active,
        'tab': tab,
        'form': form,
        'quota_form': quota_form,
        'quota_policy': {
            'limit': policy_limit,
            'caption': (
                'max calls per visitor · UTC day'
                if policy_limit
                else '0 = no per-visitor cap'
            ),
        },
        'resolved': {
            'openai_model': agent_config.get_openai_model(),
            'gemini_model': agent_config.get_gemini_model(),
            'deepseek_model': agent_config.get_deepseek_model(),
            'openrouter_model': agent_config.get_openrouter_model(),
            'openai_key_masked': masked['openai'],
            'gemini_key_masked': masked['gemini'],
            'deepseek_key_masked': masked['deepseek'],
            'openrouter_key_masked': masked['openrouter'],
        },
        'usage': {
            'total': agg['total'] or 0,
            'errors': agg['errors'] or 0,
            'tokens': agg['tokens'] or 0,
            'by_purpose': by_purpose,
            'recent': recent.order_by('-created_at')[:12],
        },
        'email_tab': etab,
        'email_status': email_status,
        'smtp_form': smtp_form,
        'imap_form': imap_form,
    }


def _redirect_settings_email(e: str = 'smtp') -> str:
    return f"{reverse('settings')}?section=email&e={e}"



@staff_required
def agent_settings_view(request):
    if request.method == 'POST':
        action = request.POST.get('action') or 'save'
        provider = request.POST.get('provider') or ''
        row = AgentSettings.load()

        if action == 'save_email':
            email_row = EmailSettings.load()
            channel = request.POST.get('channel') or ''
            if channel == 'smtp':
                sform = SmtpForm(request.POST, settings_row=email_row)
                if sform.is_valid():
                    er = sform.save()
                    er.updated_by = request.user
                    er.save()
                    messages.success(request, 'SMTP settings saved.')
                    return redirect(_redirect_settings_email('smtp'))
                return render(request, 'account/settings.html', _settings_context(
                    request, email_tab='smtp', smtp_form=sform,
                ))
            if channel == 'imap':
                iform = ImapForm(request.POST, settings_row=email_row)
                if iform.is_valid():
                    er = iform.save()
                    er.updated_by = request.user
                    er.save()
                    messages.success(request, 'IMAP settings saved.')
                    return redirect(_redirect_settings_email('imap'))
                return render(request, 'account/settings.html', _settings_context(
                    request, email_tab='imap', imap_form=iform,
                ))
            messages.error(request, 'Unknown email channel.')
            return redirect(_redirect_settings_email())

        if action == 'email_smtp_selftest':
            ok, msg = smtp_selftest()
            if ok:
                messages.success(request, f'SMTP: {msg}')
            else:
                messages.error(request, f'SMTP: {msg}')
            return redirect(_redirect_settings_email('smtp'))

        if action == 'email_imap_selftest':
            ok, msg = imap_selftest()
            if ok:
                messages.success(request, f'IMAP: {msg}')
            else:
                messages.error(request, f'IMAP: {msg}')
            return redirect(_redirect_settings_email('imap'))

        if action == 'email_send_test':
            addr = (request.POST.get('test_to') or '').strip()
            try:
                result = send_test_to(addr)
                messages.success(
                    request,
                    f'Test email sent to {addr} (Message-ID {result.message_id}).',
                )
            except SendFailed as exc:
                messages.error(request, str(exc))
            except Exception as exc:
                messages.error(request, f'{type(exc).__name__}: {exc}')
            return redirect(_redirect_settings_email('smtp'))

        if action == 'email_poll_now':
            email_row = EmailSettings.load()
            if not email_row.imap_enabled:
                messages.error(request, 'Enable IMAP and save before polling.')
                return redirect(_redirect_settings_email('imap'))
            processed = 0
            errors = 0
            try:
                for fm in fetch_unseen(limit=50):
                    processed += 1
                    try:
                        intake_raw(fm.raw)
                    except Exception:
                        errors += 1
            except ImapError as exc:
                email_row.last_poll_at = timezone.now()
                email_row.last_poll_status = f'error: {exc}'
                email_row.save(update_fields=['last_poll_at', 'last_poll_status'])
                messages.error(request, f'Poll failed: {exc}')
                return redirect(_redirect_settings_email('imap'))
            email_row.last_poll_at = timezone.now()
            email_row.last_poll_status = (
                f'ok ({processed} processed, {errors} intake errors)'
                if errors else f'ok ({processed} processed)'
            )
            email_row.save(update_fields=['last_poll_at', 'last_poll_status'])
            messages.success(request, f'Polled IMAP: {processed} message(s).')
            return redirect(_redirect_settings_email('imap'))

        if action == 'activate' and provider in _VALID_PROVIDERS:
            row.llm_provider = provider
            row.updated_by = request.user
            row.save()
            messages.success(request, f'{provider.title()} is now active.')
            return redirect(f"{reverse('settings')}?section=ai&p={provider}")

        if action == 'revoke' and provider in _VALID_PROVIDERS:
            setattr(row, f'{provider}_api_key', '')
            row.updated_by = request.user
            row.save()
            messages.success(request, f'{provider.title()} key cleared.')
            return redirect(f"{reverse('settings')}?section=ai&p={provider}")

        if action == 'save' and provider in _VALID_PROVIDERS:
            form = ProviderForm(request.POST, provider=provider, settings_row=row)
            if form.is_valid():
                row = form.save()
                row.updated_by = request.user
                row.save()
                messages.success(request, f'{provider.title()} settings saved.')
                return redirect(f"{reverse('settings')}?section=ai&p={provider}")
            return render(request, 'account/settings.html', _settings_context(
                request, provider=provider, form=form,
            ))

        if action == 'save_quota':
            quota_form = QuotaForm(request.POST, settings_row=row)
            if quota_form.is_valid():
                row = quota_form.save()
                row.updated_by = request.user
                row.save()
                messages.success(request, 'Daily AI quota saved.')
                return redirect(f"{reverse('settings')}?section=ai")
            return render(request, 'account/settings.html', _settings_context(
                request, quota_form=quota_form,
            ))

        if action == 'test':
            if llm_client.is_configured():
                reply = llm_client.chat_text_completion(
                    system='Reply with exactly: ok',
                    user='Connection test',
                    temperature=0,
                    purpose='test',
                    user_id=request.user.pk,
                )
                if reply:
                    messages.success(
                        request,
                        f'{agent_config.get_provider().title()} replied: {reply[:120]}',
                    )
                else:
                    messages.error(
                        request,
                        'The provider is configured, but the test call returned no text.',
                    )
            else:
                messages.error(request, 'No API key is configured for the active provider.')
            return redirect(f"{reverse('settings')}?section=ai")

        messages.error(request, 'Unknown settings action.')
        return redirect('settings')

    return render(request, 'account/settings.html', _settings_context(request))
