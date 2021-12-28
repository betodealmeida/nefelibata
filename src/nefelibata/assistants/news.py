"""
Assistant for fetching a random news headline.
"""

import logging
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

from aiohttp import ClientSession

from nefelibata.announcers.base import Scope
from nefelibata.assistants.base import Assistant
from nefelibata.config import Config
from nefelibata.post import Post

_logger = logging.getLogger(__name__)


DEFAULT_MAX_AGE = timedelta(days=1)


class NewsAssistant(Assistant):
    """
    Assistant for fetching a random news headline.
    """

    name = "news"
    scopes = [Scope.POST]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        root: Path,
        config: Config,
        api_key: str,
        country: str = "us",
        max_age: timedelta = DEFAULT_MAX_AGE,
        **kwargs: Any
    ):
        super().__init__(root, config, **kwargs)

        self.api_key = api_key
        self.country = country
        self.max_age = max_age

    async def get_post_metadata(self, post: Post) -> Dict[str, Any]:
        if datetime.now(tz=timezone.utc) - post.timestamp > self.max_age:
            return {}

        params = {
            "country": self.country,
            "apiKey": self.api_key,
        }

        async with ClientSession() as session:
            _logger.info("Fetching a random news headline")
            async with session.get(
                "https://newsapi.org/v2/top-headlines",
                params=params,
            ) as response:
                payload = await response.json()
                articles = payload["articles"]
                return random.choice(articles)
