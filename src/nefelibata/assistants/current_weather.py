import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import requests
from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.post import Post
from nefelibata.utils import json_storage

_logger = logging.getLogger(__name__)


MAX_AGE = timedelta(days=1)


class CurrentWeatherAssistant(Assistant):

    scopes = [Scope.POST]

    def process_post(self, post: Post, force: bool = False) -> None:
        post_directory = post.file_path.parent
        storage = post_directory / "weather.json"
        if storage.exists() and not force:
            return

        post_age = datetime.now(tz=timezone.utc) - post.date
        if post_age > MAX_AGE:
            return

        with json_storage(storage) as weather:
            response = requests.get("https://wttr.in/?format=j1&m")
            weather.update(response.json())

        # touch file to ensure it rebuilds with the weather info
        post.file_path.touch()
