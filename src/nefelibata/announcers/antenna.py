"""
An Antenna (gemini://warmedal.se/~antenna/) announcer.
"""

import logging

from nefelibata.announcers.gemlog import GemlogAnnouncer

_logger = logging.getLogger(__name__)


class AntennaAnnouncer(GemlogAnnouncer):

    """
    An Antenna (gemini://warmedal.se/~antenna/) announcer.

    This requires the Gemini builder, and assumes that the Gemlog feed is
    at ``{builder.home}/feed{builder.extension}``.
    """

    name = "Antenna"
    url = "gemini://warmedal.se/~antenna/"
    submit_url = "gemini://warmedal.se/~antenna/submit?"
    logger = _logger
