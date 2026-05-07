"""Inbound filters (headers + light content). No ML — first match wins."""

from __future__ import annotations

from typing import Callable

from .parser import ParsedEmail


def _auto_submitted(msg: ParsedEmail) -> str | None:
    val = (msg.headers.get('auto-submitted') or '').lower()
    if val and val != 'no':
        return 'header:auto-submitted'
    return None


def _precedence_bulk(msg: ParsedEmail) -> str | None:
    val = (msg.headers.get('precedence') or '').lower()
    if val in {'bulk', 'junk', 'list'}:
        return 'header:precedence-bulk'
    return None


def _mailing_list(msg: ParsedEmail) -> str | None:
    for key in ('list-id', 'list-unsubscribe', 'list-post'):
        if msg.headers.get(key):
            return 'header:mailing-list'
    return None


def _mailer_daemon(msg: ParsedEmail) -> str | None:
    addr = (msg.from_email or '').lower()
    local = addr.split('@', 1)[0] if '@' in addr else addr
    if local in {'mailer-daemon', 'postmaster'}:
        return 'header:mailer-daemon'
    return None


def _noreply(msg: ParsedEmail) -> str | None:
    addr = (msg.from_email or '').lower()
    local = addr.split('@', 1)[0] if '@' in addr else addr
    noreply_locals = {'noreply', 'no-reply', 'donotreply', 'do-not-reply'}
    if local in noreply_locals or local.startswith('noreply') or local.startswith('no-reply'):
        return 'header:noreply'
    return None


def _empty_body(msg: ParsedEmail) -> str | None:
    text = (msg.best_body or '').strip()
    if len(text) < 3:
        return 'content:empty-body'
    return None


L1_RULES: list[Callable[[ParsedEmail], str | None]] = [
    _auto_submitted,
    _precedence_bulk,
    _mailing_list,
    _mailer_daemon,
    _noreply,
]

L2_RULES: list[Callable[[ParsedEmail], str | None]] = [
    _empty_body,
]


def run_filters(msg: ParsedEmail) -> str | None:
    for rule in (*L1_RULES, *L2_RULES):
        code = rule(msg)
        if code:
            return code
    return None
