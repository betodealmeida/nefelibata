"""
Assistant for computing reading time.
"""

import math
from typing import Any, Dict

from nefelibata.announcers.base import Scope
from nefelibata.assistants.base import Assistant
from nefelibata.post import Post


class ReadingTimeAssistant(Assistant):
    """
    An assistant for computing post reading time.

    This is based on a formula supposedly used by Medium:

        https://www.quora.com/How-does-Medium-determine-an-article%E2%80%99s-estimated-read-time/answer/Alan-Hamlett
    """

    name = "reading_time"
    scopes = [Scope.POST]

    async def get_post_metadata(self, post: Post) -> Dict[str, Any]:
        num_images = len(
            [
                enclosure
                for enclosure in post.enclosures
                if enclosure.type.startswith("image")
            ],
        )
        num_words = len(post.content.split(" "))
        image_weight = max(13 - num_images, 3)
        seconds = num_words / 265 * 60 + image_weight * num_images
        minutes = math.ceil(seconds / 60)

        return {
            "words": num_words,
            "images": num_images,
            "total_seconds": seconds,
            "total_minutes": minutes,
        }
