"""
Assistant for fetching the current weather.
"""

import logging
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


class CurrentWeatherAssistant(Assistant):
    """
    An assistant for fetching the current weather.
    """

    name = "current_weather"
    scopes = [Scope.POST]

    def __init__(
        self,
        root: Path,
        config: Config,
        max_age: timedelta = DEFAULT_MAX_AGE,
        **kwargs: Any
    ):
        super().__init__(root, config, **kwargs)

        self.max_age = max_age

    async def get_post_metadata(self, post: Post) -> Dict[str, Any]:
        if datetime.now(tz=timezone.utc) - post.timestamp > self.max_age:
            return {}

        async with ClientSession() as session:
            _logger.info("Fetching current weather information")
            async with session.get("https://wttr.in/?format=j1&m") as response:
                return await response.json()
