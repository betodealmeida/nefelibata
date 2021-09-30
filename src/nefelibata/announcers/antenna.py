"""
An Antenna (gemini://warmedal.se/~antenna/) announcer.
"""

from nefelibata.announcers.gemlog import GemlogAnnouncer


class AntennaAnnouncer(GemlogAnnouncer):

    """
    An Antenna (gemini://warmedal.se/~antenna/) announcer.

    This requires the Gemini builder, and assumes that the Gemlog feed is
    at ``{builder.home}/feed{builder.extension}``.
    """

    name = "Antenna"
    uri = "gemini://warmedal.se/~antenna/"
    submit_uri = "gemini://warmedal.se/~antenna/submit?"
