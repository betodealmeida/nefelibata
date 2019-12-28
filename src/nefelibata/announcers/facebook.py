import logging
from typing import Any, Dict

from bs4 import BeautifulSoup
import facebook

from nefelibata.announcers import Announcer
from nefelibata.post import Post

_logger = logging.getLogger("nefelibata")


class FacebookAnnouncer(Announcer):
    def __init__(
        self, post: Post, config: Dict[str, Any], access_token: str, page_id: int
    ):
        self.post = post
        self.config = config
        self.page_id = page_id

        self.client = facebook.GraphAPI(access_token=access_token)

    def announce(self) -> None:
        """Publish the summary of a post to Facebook.

        Facebook doesn't have a publish API, so we need to open the browser
        with a link for the user. Once the user has posted, we have the post
        id so we can store if for later, when collecting replies.

        """
        if "facebook-url" not in self.post.parsed:
            _logger.info("Announcing post on Facebook")

            soup = BeautifulSoup(self.post.html, "html.parser")
            if soup.img:
                picture = soup.img.attrs.get("src")
            else:
                picture = None

            response = self.client.put_object(
                parent_object=self.page_id,
                connection_name="feed",
                message=self.post.summary,
                link="%s/%s" % (self.config["url"], self.post.url),
                name=self.post.title,
                picture=picture,
            )

            print(response)
            self.post.post["facebook-url"] = response["id"]
            self.post.save()
            _logger.info("Success!")

    def collect(self) -> None:
        pass
