"""
An announcer that saves the post and blog in https://archive.org/.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from nefelibata.announcers.base import Announcement, Announcer, Scope
from nefelibata.post import Post
from nefelibata.utils import archive_urls

_logger = logging.getLogger(__name__)


class ArchiveBlogAnnouncer(Announcer):

    """
    An announcer that saves the post and blog in https://archive.org/.
    """

    scopes = [Scope.POST, Scope.SITE]

    async def announce_post(self, post: Post) -> Optional[Announcement]:
        urls = [builder.absolute_url(post) for builder in self.builders]
        saved_urls = await archive_urls(urls)
        if saved_urls:
            return Announcement(
                url="https://web.archive.org/save/",
                timestamp=datetime.now(timezone.utc),
            )
        return None

    async def announce_site(self) -> Optional[Announcement]:
        urls = [builder.home for builder in self.builders]
        saved_urls = await archive_urls(urls)
        if saved_urls:
            return Announcement(
                url="https://web.archive.org/save/",
                timestamp=datetime.now(timezone.utc),
            )
        return None
