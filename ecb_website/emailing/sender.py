"""Outbound SMTP — send LeadMessage drafts and test messages."""

from __future__ import annotations

import email.utils
import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Iterable

from django.utils import timezone

from leads.models import LeadMessage

from . import config as email_config

logger = logging.getLogger(__name__)


class SendFailed(Exception):
    pass


@dataclass
class SendResult:
    message_id: str


def _clean_address_list(addrs: Iterable[str] | str | None) -> list[str]:
    if not addrs:
        return []
    if isinstance(addrs, str):
        addrs = addrs.split(',')
    out: list[str] = []
    for raw in addrs:
        a = (raw or '').strip()
        if a and '@' in a and a not in out:
            out.append(a)
    return out


def _apply_signature(body: str, signature: str) -> str:
    body = (body or '').rstrip()
    signature = (signature or '').strip()
    if not signature:
        return body
    if signature in body:
        return body
    return f'{body}\n\n{signature}\n'


def _build_mime(
    *,
    draft: LeadMessage,
    smtp_cfg,
    message_id: str,
    cc: list[str],
    bcc: list[str],
    signature: str,
) -> EmailMessage:
    msg = EmailMessage()
    from_display = (
        email.utils.formataddr((smtp_cfg.from_name, smtp_cfg.from_address))
        if smtp_cfg.from_name else smtp_cfg.from_address
    )
    msg['From'] = from_display
    msg['To'] = draft.lead.email
    if cc:
        msg['Cc'] = ', '.join(cc)
    if bcc:
        msg['Bcc'] = ', '.join(bcc)
    msg['Subject'] = draft.subject or '(no subject)'
    msg['Message-ID'] = message_id
    msg['Date'] = email.utils.format_datetime(timezone.now())
    if draft.in_reply_to:
        msg['In-Reply-To'] = draft.in_reply_to
        msg['References'] = draft.in_reply_to
    msg.set_content(_apply_signature(draft.body, signature))
    return msg


def _smtp_connection(cfg):
    if cfg.use_tls:
        client = smtplib.SMTP(cfg.host, cfg.port, timeout=20)
        client.ehlo()
        client.starttls(context=ssl.create_default_context())
        client.ehlo()
    else:
        client = smtplib.SMTP(cfg.host, cfg.port, timeout=20)
        client.ehlo()
    if cfg.username:
        client.login(cfg.username, cfg.password)
    return client


def send_draft(
    draft: LeadMessage,
    *,
    cc: Iterable[str] | str | None = None,
    bcc: Iterable[str] | str | None = None,
) -> SendResult:
    if draft.status != LeadMessage.Status.DRAFT:
        raise SendFailed(f'Only DRAFT messages can be sent (was {draft.status}).')

    cfg = email_config.get_smtp()
    if not cfg.configured:
        raise SendFailed('SMTP is not configured (host and from-address required).')
    if not cfg.enabled:
        raise SendFailed('SMTP is configured but not enabled. Toggle it in Settings.')
    if not draft.lead.email:
        raise SendFailed('Lead has no email address on file.')

    signature = email_config.get_signature()
    cc_list = _clean_address_list(cc)
    bcc_list = _clean_address_list(bcc)

    domain = (
        cfg.from_address.split('@', 1)[-1] if '@' in cfg.from_address else 'local'
    )
    message_id = email.utils.make_msgid(domain=domain)

    mime = _build_mime(
        draft=draft,
        smtp_cfg=cfg,
        message_id=message_id,
        cc=cc_list,
        bcc=bcc_list,
        signature=signature,
    )

    try:
        with _smtp_connection(cfg) as client:
            refused = client.send_message(mime)
    except smtplib.SMTPException as exc:
        logger.warning('SMTP error sending draft %s: %s', draft.pk, exc)
        raise SendFailed(f'SMTP error: {exc}') from exc
    except (OSError, ssl.SSLError) as exc:
        logger.warning('SMTP transport error for draft %s: %s', draft.pk, exc)
        raise SendFailed(f'Connection error: {exc}') from exc

    if refused:
        raise SendFailed(f'Server refused recipients: {refused}')

    return SendResult(message_id=message_id)


def record_send_failure(draft: LeadMessage, err: str) -> None:
    meta = dict(draft.metadata or {})
    meta['send_attempts'] = int(meta.get('send_attempts') or 0) + 1
    meta['last_error'] = (err or '')[:500]
    meta['last_error_at'] = timezone.now().isoformat()
    draft.metadata = meta
    draft.save(update_fields=['metadata'])


def clear_send_error(draft: LeadMessage) -> None:
    meta = dict(draft.metadata or {})
    meta.pop('last_error', None)
    meta.pop('last_error_at', None)
    draft.metadata = meta


def send_test_to(addr: str) -> SendResult:
    cfg = email_config.get_smtp()
    if not cfg.configured:
        raise SendFailed('SMTP is not configured.')
    if not cfg.enabled:
        raise SendFailed('SMTP is disabled — enable it and save first.')
    addr = (addr or '').strip()
    if not addr or '@' not in addr:
        raise SendFailed('Please provide a valid recipient address.')

    domain = (
        cfg.from_address.split('@', 1)[-1] if '@' in cfg.from_address else 'local'
    )
    message_id = email.utils.make_msgid(domain=domain)

    msg = EmailMessage()
    from_display = (
        email.utils.formataddr((cfg.from_name, cfg.from_address))
        if cfg.from_name else cfg.from_address
    )
    msg['From'] = from_display
    msg['To'] = addr
    msg['Subject'] = 'Executive Coach Builders — SMTP test'
    msg['Message-ID'] = message_id
    msg['Date'] = email.utils.format_datetime(timezone.now())
    msg.set_content(
        'If you are reading this, SMTP settings work end-to-end for the portal.'
    )

    try:
        with _smtp_connection(cfg) as client:
            refused = client.send_message(msg)
    except smtplib.SMTPException as exc:
        raise SendFailed(f'SMTP error: {exc}') from exc
    except (OSError, ssl.SSLError) as exc:
        raise SendFailed(f'Connection error: {exc}') from exc

    if refused:
        raise SendFailed(f'Server refused: {refused}')
    return SendResult(message_id=message_id)


def smtp_selftest() -> tuple[bool, str]:
    cfg = email_config.get_smtp()
    if not cfg.configured:
        return False, 'Host and from-address are required.'
    try:
        with _smtp_connection(cfg) as client:
            code, _ = client.noop()
            return True, f'{cfg.host}:{cfg.port} OK (NOOP={code})'
    except Exception as exc:
        return False, f'{type(exc).__name__}: {exc}'
