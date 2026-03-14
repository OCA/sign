# Copyright 2025 Keboola
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# -*- coding: utf-8 -*-
import logging

from . import models

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Backfill sent_date for existing sent requests on fresh install."""
    _backfill_sent_date(env)


def _backfill_sent_date(env):
    """Set sent_date = create_date for requests already in '0_sent' state.

    When the module is installed on a database with existing sign requests
    that were sent before the module was available, sent_date is NULL.
    Without sent_date, next_reminder_date cannot be computed and reminders
    never fire.
    """
    env.cr.execute("""
        UPDATE sign_oca_request
        SET sent_date = create_date
        WHERE state = '0_sent'
          AND sent_date IS NULL
    """)
    updated = env.cr.rowcount
    if updated:
        _logger.info(
            "Backfilled sent_date for %d existing sign request(s).",
            updated,
        )
        # Trigger recomputation of stored next_reminder_date
        requests = env["sign.oca.request"].search(
            [
                ("state", "=", "0_sent"),
                ("reminder_enabled", "=", True),
            ]
        )
        if requests:
            requests._compute_next_reminder_date()
            _logger.info(
                "Recomputed next_reminder_date for %d request(s).",
                len(requests),
            )
