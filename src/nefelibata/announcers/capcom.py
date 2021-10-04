"""
A CAPCOM (gemini://gemini.circumlunar.space/capcom/) announcer.
"""

import logging
from datetime import timedelta

from nefelibata.announcers.gemlog import GemlogAnnouncer

_logger = logging.getLogger(__name__)


class CAPCOMAnnouncer(GemlogAnnouncer):

    """
    A CAPCOM (gemini://gemini.circumlunar.space/capcom/) announcer.

    This requires the Gemini builder, and assumes that the Gemlog feed is
    at ``{builder.home}/feed{builder.extension}``.
    """

    name = "CAPCOM"
    url = "gemini://gemini.circumlunar.space/capcom/"
    submit_url = "gemini://gemini.circumlunar.space/capcom/submit?"
    grace_seconds = timedelta(days=365).total_seconds()
    logger = _logger
