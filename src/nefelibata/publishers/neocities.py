import logging
import mimetypes
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import requests
from nefelibata.publishers import Publisher

_logger = logging.getLogger(__name__)


blocklist = [".mkd"]


class NeocitiesPublisher(Publisher):

    """A publisher that uploads the weblog to Neocities."""

    def __init__(
        self,
        root: Path,
        config: Dict[str, Any],
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        super().__init__(root, config)

        if bool(username and password) == (api_key is not None):
            raise Exception(
                "You must provide exactly ONE of username/password or API key",
            )

        if username and password:
            response = requests.get(
                f"https://{username}:{password}@neocities.org/api/key",
            )
            payload = response.json()
            api_key = payload["api_key"]
            _logger.warning(
                f"Your API key is {api_key}, please remove the username/password from the configuration and add the API key",
            )

        self.headers = {"Authorization": f"Bearer {api_key}"}

    def publish(self, force: bool = False) -> None:
        # store file with the last time weblog was published
        last_published_file = self.root / "last_published"
        if last_published_file.exists():
            last_published = last_published_file.stat().st_mtime
        else:
            last_published = 0

        build = self.root / "build"
        filenames: List[Tuple[Path, str]] = []
        for path in self.find_modified_files(force, last_published):
            if path.suffix not in blocklist:
                key = str(path.relative_to(build))
                filenames.append((path, key))

        # NeoCities API expects a dict in the following format:
        # { name_on_server: <file_object> }
        args = {pair[1]: open(pair[0], "rb") for pair in filenames}
        if not args:
            return

        url = "https://neocities.org/api/upload"
        response = requests.post(url, files=args, headers=self.headers)
        response.raise_for_status()

        # update last published
        last_published_file.touch()
