"""
A Neocities publisher.
"""
import logging
from datetime import datetime, timezone
from io import BufferedReader
from pathlib import Path
from typing import Any, Dict, Optional

from aiohttp import ClientResponseError, ClientSession

from nefelibata.config import Config
from nefelibata.publishers.base import Publisher, Publishing

_logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {
    "asc",
    "atom",
    "bin",
    "css",
    "csv",
    "dae",
    "eot",
    "epub",
    "geojson",
    "gif",
    "gltf",
    "htm",
    "html",
    "ico",
    "jpeg",
    "jpg",
    "js",
    "json",
    "key",
    "kml",
    "knowl",
    "less",
    "manifest",
    "markdown",
    "md",
    "mf",
    "mid",
    "midi",
    "mtl",
    "obj",
    "opml",
    "otf",
    "pdf",
    "pgp",
    "png",
    "rdf",
    "rss",
    "sass",
    "scss",
    "svg",
    "text",
    "tsv",
    "ttf",
    "txt",
    "webapp",
    "webmanifest",
    "webp",
    "woff",
    "woff2",
    "xcf",
    "xml",
}


async def get_api_key(username: str, password: str) -> str:
    """
    Fetch the API key for a given username/password.
    """
    url = f"https://{username}:{password}@neocities.org/api/key"

    async with ClientSession() as session:
        async with session.get(url) as response:
            payload = await response.json()
            api_key = payload["api_key"]
            _logger.warning(
                "Your API key is %s, please remove the username/password "
                "from the configuration and add the API key",
                api_key,
            )

    return api_key


class NeocitiesPublisher(Publisher):

    """
    A publisher that uploads the blog to Neocities.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        root: Path,
        config: Config,
        path: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(root, config, path, **kwargs)

        if bool(username or password) == (api_key is not None):
            raise Exception(
                "You MUST provide exactly ONE of username/password or API key"
            )

        self.username = username
        self.password = password
        self.api_key = api_key

    async def publish(
        self,
        since: Optional[datetime] = None,
        force: bool = False,
    ) -> Optional[Publishing]:
        if self.api_key is None:
            self.api_key = await get_api_key(self.username, self.password)

        modified_files = list(self.find_modified_files(force, since))

        build = self.root / "build" / self.path
        files: Dict[str, BufferedReader] = {}
        for path in modified_files:
            if path.suffix.lstrip(".") in ALLOWED_EXTENSIONS:
                key = str(path.relative_to(build))
                files[key] = open(path, "rb")  # pylint: disable=consider-using-with
            else:
                _logger.warning("File %s cannot be uploaded", path)

        if not files:
            return

        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = "https://neocities.org/api/upload"
        async with ClientSession() as session:
            async with session.post(url, data=files, headers=headers) as response:
                try:
                    response.raise_for_status()
                except ClientResponseError:
                    payload = await response.json()
                    _logger.error(payload["message"])
                    return None

        for file in files.values():
            file.close()

        if modified_files:
            return Publishing(timestamp=datetime.now(timezone.utc))

        return None
