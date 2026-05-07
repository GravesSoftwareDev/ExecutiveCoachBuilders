"""Inbound pipeline: filter → match → LeadMessage + IncomingEmail audit row."""

from __future__ import annotations

import logging
from typing import Any

from django.db import transaction

from leads.models import Lead, LeadMessage

from . import config as email_config
from .filters import run_filters
from .matcher import match
from .models import IncomingEmail
from .parser import ParsedEmail, parse_raw_email

logger = logging.getLogger(__name__)


def _log_inbound_on_lead(
    *,
    lead: Lead,
    msg: ParsedEmail,
    in_reply_to_obj: LeadMessage | None = None,
) -> LeadMessage:
    return LeadMessage.objects.create(
        lead=lead,
        direction=LeadMessage.Direction.IN,
        channel=LeadMessage.Channel.EMAIL,
        status=LeadMessage.Status.RECEIVED,
        subject=msg.subject,
        body=msg.best_body,
        message_id=msg.message_id,
        in_reply_to=(
            in_reply_to_obj.message_id if in_reply_to_obj else msg.in_reply_to
        ),
        from_email=msg.from_email,
        to_email=msg.to_email,
        metadata={
            'source': 'email_inbound',
            'from_name': msg.from_name,
            'attachment_names': msg.attachment_names,
        },
    )


def _log_internal_reply_on_lead(
    *,
    lead: Lead,
    msg: ParsedEmail,
    replied_to: LeadMessage | None,
) -> LeadMessage:
    return LeadMessage.objects.create(
        lead=lead,
        direction=LeadMessage.Direction.OUT,
        channel=LeadMessage.Channel.EMAIL,
        status=LeadMessage.Status.SENT,
        subject=msg.subject,
        body=msg.best_body,
        message_id=msg.message_id,
        in_reply_to=(replied_to.message_id if replied_to else msg.in_reply_to),
        from_email=msg.from_email,
        to_email=msg.to_email,
        sent_at=msg.received_at,
        metadata={
            'source': 'email_internal_reply',
            'attachment_names': msg.attachment_names,
        },
    )


def _store_incoming(
    msg: ParsedEmail,
    *,
    status: str,
    filter_reason: str = '',
    lead: Lead | None = None,
    linked_message: LeadMessage | None = None,
) -> IncomingEmail:
    defaults: dict[str, Any] = {
        'in_reply_to': msg.in_reply_to,
        'references': msg.references,
        'from_email': msg.from_email or '',
        'from_name': msg.from_name,
        'to_email': msg.to_email,
        'subject': msg.subject[:998],
        'body_text': msg.body_text,
        'body_html': msg.body_html,
        'raw_headers': msg.headers,
        'attachment_names': msg.attachment_names,
        'received_at': msg.received_at,
        'status': status,
        'filter_reason': filter_reason,
        'lead': lead,
        'linked_message': linked_message,
    }
    obj, created = IncomingEmail.objects.get_or_create(
        message_id=msg.message_id,
        defaults=defaults,
    )
    if not created:
        logger.info('Skipping duplicate inbound Message-ID %s', msg.message_id)
    return obj


@transaction.atomic
def intake_parsed(msg: ParsedEmail) -> IncomingEmail:
    if IncomingEmail.objects.filter(message_id=msg.message_id).exists():
        return IncomingEmail.objects.get(message_id=msg.message_id)

    filter_code = run_filters(msg)
    if filter_code:
        return _store_incoming(
            msg,
            status=IncomingEmail.Status.FILTERED,
            filter_reason=filter_code,
        )

    internal_domains = email_config.get_internal_domains()
    result = match(msg, internal_domains=internal_domains)

    if result.kind == 'thread_match' and result.lead is not None:
        lm = _log_inbound_on_lead(
            lead=result.lead, msg=msg, in_reply_to_obj=result.replied_to,
        )
        return _store_incoming(
            msg,
            status=IncomingEmail.Status.LINKED,
            lead=result.lead,
            linked_message=lm,
        )

    if result.kind == 'sender_match' and result.lead is not None:
        lm = _log_inbound_on_lead(lead=result.lead, msg=msg)
        return _store_incoming(
            msg,
            status=IncomingEmail.Status.LINKED,
            lead=result.lead,
            linked_message=lm,
        )

    if result.kind == 'internal_reply':
        if result.lead is not None:
            lm = _log_internal_reply_on_lead(
                lead=result.lead, msg=msg, replied_to=result.replied_to,
            )
            return _store_incoming(
                msg,
                status=IncomingEmail.Status.INTERNAL_REPLY,
                lead=result.lead,
                linked_message=lm,
            )
        return _store_incoming(
            msg,
            status=IncomingEmail.Status.PENDING,
            filter_reason='internal_reply:no_thread',
        )

    return _store_incoming(msg, status=IncomingEmail.Status.PENDING)


def intake_raw(raw: bytes | str) -> IncomingEmail:
    return intake_parsed(parse_raw_email(raw))
