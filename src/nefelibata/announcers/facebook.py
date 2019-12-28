import logging
from typing import Any, Dict, List

from bs4 import BeautifulSoup
import facebook

from nefelibata.announcers import Announcer
from nefelibata.post import Post

_logger = logging.getLogger("nefelibata")


class FacebookAnnouncer(Announcer):

    name = "Facebook"
    url_header = "facebook-url"

    def __init__(
        self, post: Post, config: Dict[str, Any], access_token: str, page_id: int
    ):
        self.post = post
        self.config = config
        self.page_id = page_id

        self.client = facebook.GraphAPI(access_token=access_token)

    def announce(self) -> str:
        """Publish the summary of a post to Facebook.
        """
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
        _logger.info("Success!")

        return response["id"]  # XXX

    def collect(self) -> List[Dict[str, Any]]:
        pass
