"""Resolve SMTP/IMAP config: DB row > environment variables > defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass

SMTP_DEFAULT_PORT = 587
IMAP_DEFAULT_PORT = 993


@dataclass(frozen=True)
class SmtpConfig:
    enabled: bool
    host: str
    port: int
    username: str
    password: str
    use_tls: bool
    from_address: str
    from_name: str

    @property
    def configured(self) -> bool:
        return bool(self.host and self.from_address)


@dataclass(frozen=True)
class ImapConfig:
    enabled: bool
    host: str
    port: int
    username: str
    password: str
    use_ssl: bool
    folder: str

    @property
    def configured(self) -> bool:
        return bool(self.host and self.username)


def _row():
    try:
        from emailing.models import EmailSettings
        return EmailSettings.objects.filter(pk=1).first()
    except Exception:
        return None


def _pick(db_value, env_name: str, default: str = '') -> str:
    if db_value:
        return str(db_value)
    return (os.environ.get(env_name, default) or default).strip()


def _pick_int(db_value, env_name: str, default: int) -> int:
    if db_value:
        try:
            return int(db_value)
        except (TypeError, ValueError):
            pass
    raw = os.environ.get(env_name, '').strip()
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return default


def _pick_bool(db_value: bool | None, env_name: str, default: bool) -> bool:
    if db_value is not None:
        return bool(db_value)
    raw = os.environ.get(env_name, '').strip().lower()
    if raw in ('1', 'true', 'yes', 'on'):
        return True
    if raw in ('0', 'false', 'no', 'off'):
        return False
    return default


def get_smtp() -> SmtpConfig:
    row = _row()
    return SmtpConfig(
        enabled=bool(row and row.smtp_enabled) or _pick_bool(None, 'SMTP_ENABLED', False),
        host=_pick(row and row.smtp_host, 'SMTP_HOST'),
        port=_pick_int(row and row.smtp_port, 'SMTP_PORT', SMTP_DEFAULT_PORT),
        username=_pick(row and row.smtp_username, 'SMTP_USERNAME'),
        password=_pick(row and row.smtp_password, 'SMTP_PASSWORD'),
        use_tls=_pick_bool(
            row.smtp_use_tls if row else None, 'SMTP_USE_TLS', True
        ),
        from_address=_pick(row and row.from_address, 'SMTP_FROM_ADDRESS'),
        from_name=_pick(row and row.from_name, 'SMTP_FROM_NAME'),
    )


def get_imap() -> ImapConfig:
    row = _row()
    return ImapConfig(
        enabled=bool(row and row.imap_enabled) or _pick_bool(None, 'IMAP_ENABLED', False),
        host=_pick(row and row.imap_host, 'IMAP_HOST'),
        port=_pick_int(row and row.imap_port, 'IMAP_PORT', IMAP_DEFAULT_PORT),
        username=_pick(row and row.imap_username, 'IMAP_USERNAME'),
        password=_pick(row and row.imap_password, 'IMAP_PASSWORD'),
        use_ssl=_pick_bool(
            row.imap_use_ssl if row else None, 'IMAP_USE_SSL', True
        ),
        folder=_pick(row and row.imap_folder, 'IMAP_FOLDER', 'INBOX') or 'INBOX',
    )


def get_signature() -> str:
    row = _row()
    if row and row.signature:
        return row.signature
    return os.environ.get('EMAIL_SIGNATURE', '') or ''


def get_internal_domains() -> list[str]:
    row = _row()
    if row and row.internal_domains:
        return row.internal_domain_list()
    raw = os.environ.get('EMAIL_INTERNAL_DOMAINS', 'ecblimo.com').strip()
    return [d.strip().lower() for d in raw.split(',') if d.strip()]


def mask_password(pwd: str) -> str:
    if not pwd:
        return ''
    if len(pwd) <= 4:
        return '•' * len(pwd)
    return '•' * (len(pwd) - 2) + pwd[-2:]
