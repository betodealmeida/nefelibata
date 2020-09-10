import math

from bs4 import BeautifulSoup
from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.post import Post
from nefelibata.utils import modify_html

THRESHOLD_MINUTES = 2


class ReadingTimeAssistant(Assistant):

    scopes = [Scope.POST]

    def process_post(self, post: Post, force: bool = False) -> None:
        # Use formula from Medium (https://www.quora.com/How-does-Medium-determine-an-article%E2%80%99s-estimated-read-time/answer/Alan-Hamlett)
        soup = BeautifulSoup(post.html, "html.parser")
        num_images = len(soup.find_all("img"))
        num_words = len(soup.text.split(" "))
        image_weight = max(13 - num_images, 3)
        seconds = num_words / 265 * 60 + image_weight * num_images
        minutes = math.ceil(seconds / 60)

        if minutes < THRESHOLD_MINUTES:
            return

        with modify_html(post.file_path.with_suffix(".html")) as soup:
            el = soup.find(id="post-reading-time")
            if el:
                span = soup.new_tag("span")
                span.string = f"Approximate reading time: {minutes} minutes"
                el.clear()
                el.append(span)
