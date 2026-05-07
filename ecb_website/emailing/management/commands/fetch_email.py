"""Fetch UNSEEN mail via IMAP and run intake (cron / one-shot)."""

from __future__ import annotations

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from emailing.adapters.imap import ImapError, fetch_unseen
from emailing.intake import intake_raw
from emailing.models import EmailSettings


class Command(BaseCommand):
    help = 'Fetch unread email via IMAP and attach to leads where possible.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=50)
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Connect and list sizes only (no DB writes).',
        )

    def handle(self, *args, limit: int, dry_run: bool, **opts):
        settings_row = EmailSettings.load()
        if not settings_row.imap_enabled:
            self.stdout.write(self.style.WARNING('IMAP is disabled in settings.'))
            return

        processed = 0
        try:
            for fm in fetch_unseen(limit=limit):
                processed += 1
                if dry_run:
                    self.stdout.write(f'[dry-run] uid={fm.uid} ({len(fm.raw)} bytes)')
                    continue
                try:
                    row = intake_raw(fm.raw)
                    self.stdout.write(
                        f'uid={fm.uid} -> incoming#{row.pk} status={row.status}',
                    )
                except Exception:
                    logging.getLogger(__name__).exception('Intake failed uid=%s', fm.uid)
        except ImapError as exc:
            settings_row.last_poll_at = timezone.now()
            settings_row.last_poll_status = f'error: {exc}'
            settings_row.save(update_fields=['last_poll_at', 'last_poll_status'])
            raise

        settings_row.last_poll_at = timezone.now()
        settings_row.last_poll_status = f'ok ({processed} processed)'
        settings_row.save(update_fields=['last_poll_at', 'last_poll_status'])
        self.stdout.write(self.style.SUCCESS(f'Done — {processed} processed'))
