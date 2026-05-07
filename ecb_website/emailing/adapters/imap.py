"""IMAP transport: fetch UNSEEN, mark SEEN after read."""

from __future__ import annotations

import imaplib
import logging
import ssl
from dataclasses import dataclass
from typing import Iterator

from .. import config as email_config

logger = logging.getLogger(__name__)


class ImapError(Exception):
    pass


@dataclass
class FetchedMessage:
    uid: str
    raw: bytes


def _connect():
    cfg = email_config.get_imap()
    if not cfg.configured:
        raise ImapError('IMAP is not configured (host + username required).')
    if cfg.use_ssl:
        ctx = ssl.create_default_context()
        client = imaplib.IMAP4_SSL(cfg.host, cfg.port, ssl_context=ctx)
    else:
        client = imaplib.IMAP4(cfg.host, cfg.port)
    try:
        client.login(cfg.username, cfg.password)
    except imaplib.IMAP4.error as exc:
        raise ImapError(f'IMAP login failed: {exc}') from exc
    return client, cfg


def fetch_unseen(limit: int | None = 50) -> Iterator[FetchedMessage]:
    client, cfg = _connect()
    try:
        typ, _ = client.select(cfg.folder)
        if typ != 'OK':
            raise ImapError(f'SELECT {cfg.folder} failed.')

        typ, data = client.search(None, 'UNSEEN')
        if typ != 'OK':
            raise ImapError('IMAP SEARCH failed.')

        ids_raw = data[0] if data else b''
        ids = ids_raw.split() if ids_raw else []
        if limit is not None:
            ids = ids[:limit]

        for uid in ids:
            uid_s = uid.decode('ascii')
            typ, fetched = client.fetch(uid, '(RFC822)')
            if typ != 'OK' or not fetched:
                logger.warning('IMAP FETCH %s failed', uid_s)
                continue
            for part in fetched:
                if isinstance(part, tuple) and len(part) >= 2:
                    yield FetchedMessage(uid=uid_s, raw=part[1])
                    break
    finally:
        try:
            client.close()
        except Exception:
            pass
        try:
            client.logout()
        except Exception:
            pass


def imap_selftest() -> tuple[bool, str]:
    try:
        client, cfg = _connect()
    except ImapError as exc:
        return False, str(exc)
    try:
        typ, data = client.select(cfg.folder)
        if typ != 'OK':
            return False, f'SELECT {cfg.folder} failed.'
        typ, data = client.search(None, 'ALL')
        count = len(data[0].split()) if data and data[0] else 0
        return True, f'{cfg.host}:{cfg.port} OK — {count} message(s) in {cfg.folder}'
    finally:
        try:
            client.logout()
        except Exception:
            pass
