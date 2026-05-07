"""Parse raw RFC 5322 bytes into ParsedEmail (no DB / network)."""

from __future__ import annotations

import email
import email.policy
import email.utils
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone as dt_timezone
from email.message import EmailMessage

HTML_TAG = re.compile(r'<[^>]+>')


@dataclass
class ParsedEmail:
    message_id: str
    in_reply_to: str = ''
    references: str = ''
    from_email: str = ''
    from_name: str = ''
    to_email: str = ''
    subject: str = ''
    body_text: str = ''
    body_html: str = ''
    received_at: datetime = field(default_factory=lambda: datetime.now(dt_timezone.utc))
    headers: dict[str, str] = field(default_factory=dict)
    attachment_names: list[str] = field(default_factory=list)

    @property
    def best_body(self) -> str:
        if self.body_text.strip():
            return self.body_text
        if self.body_html:
            return HTML_TAG.sub(' ', self.body_html)
        return ''


def _first_address(raw: str) -> tuple[str, str]:
    if not raw:
        return ('', '')
    try:
        addrs = email.utils.getaddresses([raw])
    except Exception:
        return ('', '')
    for name, addr in addrs:
        if addr:
            return (name.strip(), addr.strip().lower())
    return ('', '')


def _parse_date(raw: str) -> datetime:
    if not raw:
        return datetime.now(dt_timezone.utc)
    try:
        parsed = email.utils.parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return datetime.now(dt_timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_timezone.utc)
    return parsed


def _ensure_message_id(raw_mid: str) -> str:
    mid = (raw_mid or '').strip()
    if mid:
        return mid
    return email.utils.make_msgid(domain='missing.message.id.local')


def parse_raw_email(raw: bytes | str) -> ParsedEmail:
    if isinstance(raw, str):
        raw = raw.encode('utf-8', errors='replace')
    msg: EmailMessage = email.message_from_bytes(raw, policy=email.policy.default)

    from_name, from_addr = _first_address(str(msg.get('From', '')))
    _, to_addr = _first_address(str(msg.get('To', '')))

    body_text = ''
    body_html = ''
    attachments: list[str] = []

    for part in msg.walk():
        ctype = part.get_content_type()
        disp = (part.get('Content-Disposition') or '').lower()
        if 'attachment' in disp:
            name = part.get_filename()
            if name:
                attachments.append(name)
            continue
        if ctype == 'text/plain' and not body_text:
            try:
                body_text = part.get_content()
            except Exception:
                body_text = (part.get_payload(decode=True) or b'').decode(
                    part.get_content_charset() or 'utf-8', errors='replace',
                )
        elif ctype == 'text/html' and not body_html:
            try:
                body_html = part.get_content()
            except Exception:
                body_html = (part.get_payload(decode=True) or b'').decode(
                    part.get_content_charset() or 'utf-8', errors='replace',
                )

    headers = {k.lower(): str(v) for k, v in msg.items()}

    return ParsedEmail(
        message_id=_ensure_message_id(str(msg.get('Message-ID', ''))),
        in_reply_to=str(msg.get('In-Reply-To', '')).strip(),
        references=str(msg.get('References', '')).strip(),
        from_email=from_addr,
        from_name=from_name,
        to_email=to_addr,
        subject=str(msg.get('Subject', '')).strip(),
        body_text=body_text or '',
        body_html=body_html or '',
        received_at=_parse_date(str(msg.get('Date', ''))),
        headers=headers,
        attachment_names=attachments,
    )
