"""
A CAPCOM (gemini://gemini.circumlunar.space/capcom/) announcer.
"""

from datetime import timedelta

from nefelibata.announcers.gemlog import GemlogAnnouncer


class CAPCOMAnnouncer(GemlogAnnouncer):

    """
    A CAPCOM (gemini://gemini.circumlunar.space/capcom/) announcer.

    This requires the Gemini builder, and assumes that the Gemlog feed is
    at ``{builder.home}/feed{builder.extension}``.
    """

    name = "CAPCOM"
    uri = "gemini://gemini.circumlunar.space/capcom/"
    submit_uri = "gemini://gemini.circumlunar.space/capcom/submit?"
    grace_seconds = timedelta(days=365).total_seconds()
