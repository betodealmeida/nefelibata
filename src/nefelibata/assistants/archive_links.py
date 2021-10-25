"""
Assistant for saving external links in https://archive.org/.
"""

import logging
from typing import Dict

from nefelibata.announcers.base import Scope
from nefelibata.assistants.base import Assistant
from nefelibata.post import Post, extract_links
from nefelibata.utils import archive_urls

_logger = logging.getLogger(__name__)


class ArchiveLinksAssistant(Assistant):

    """
    Assistant for saving external links in https://archive.org/.
    """

    name = "saved_links"
    scopes = [Scope.POST]

    async def get_post_metadata(self, post: Post) -> Dict[str, str]:
        saved_urls = await archive_urls(extract_links(post))
        return {str(k): str(v) for k, v in saved_urls.items()}
