"""Loop: run fetch_email every ``interval`` seconds."""

from __future__ import annotations

import logging
import signal
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Poll IMAP in a loop (use systemd/cron, or --once for a single run).'

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=300)
        parser.add_argument('--limit', type=int, default=50)
        parser.add_argument('--once', action='store_true')

    def handle(self, *args, interval: int, limit: int, once: bool, **opts):
        self._running = True
        signal.signal(signal.SIGTERM, self._stop)
        signal.signal(signal.SIGINT, self._stop)

        if once:
            self._tick(limit)
            return

        self.stdout.write(
            self.style.SUCCESS(f'poll_email: every {interval}s, limit={limit}'),
        )
        while self._running:
            self._tick(limit)
            for _ in range(interval):
                if not self._running:
                    break
                time.sleep(1)
        self.stdout.write('poll_email stopped')

    def _tick(self, limit: int) -> None:
        try:
            call_command('fetch_email', limit=limit, verbosity=0)
        except Exception:
            logger.exception('poll_email tick failed')

    def _stop(self, *_args) -> None:
        self._running = False
