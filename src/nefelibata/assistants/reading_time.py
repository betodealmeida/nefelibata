import math

from bs4 import BeautifulSoup

from nefelibata.assistants import Assistant
from nefelibata.assistants import Order
from nefelibata.assistants import Scope
from nefelibata.post import Post
from nefelibata.utils import json_storage

THRESHOLD_MINUTES = 2


class ReadingTimeAssistant(Assistant):

    """
    Compute reading time for a given article.

    This is based on a formula supposedly used by Medium:

        https://www.quora.com/How-does-Medium-determine-an-article%E2%80%99s-estimated-read-time/answer/Alan-Hamlett

    """

    scopes = [Scope.POST]
    order = Order.BEFORE

    def process_post(self, post: Post, force: bool = False) -> None:
        post_directory = post.file_path.parent
        storage = post_directory / "reading_time.json"
        if storage.exists() and not force:
            return

        soup = BeautifulSoup(post.html, "html.parser")
        num_images = len(soup.find_all("img"))
        num_words = len(soup.text.split(" "))
        image_weight = max(13 - num_images, 3)
        seconds = num_words / 265 * 60 + image_weight * num_images
        minutes = math.ceil(seconds / 60)

        if minutes < THRESHOLD_MINUTES:
            return

        with json_storage(storage) as payload:
            payload.update(
                {
                    "seconds": seconds,
                    "minutes": minutes,
                    "words": num_words,
                    "images": num_images,
                }
            )
