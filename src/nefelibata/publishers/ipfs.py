import logging
import mimetypes
import re
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import requests
from nefelibata.publishers import Publisher

_logger = logging.getLogger(__name__)


class IPFSPublisher(Publisher):

    """A publisher that uploads the weblog to IPFS through a remote host."""

    def __init__(
        self,
        root: Path,
        config: Dict[str, Any],
        username: Optional[str] = None,
        host: Optional[str] = None,
    ):
        super().__init__(root, config)

        self.username = username
        self.host = host

    def publish(self, force: bool = False) -> None:
        build_dir = self.root / "build"
        remote_dir = urllib.parse.urlparse(self.config["url"]).netloc

        _logger.info("Syncing content")
        subprocess.run(
            [
                "rsync",
                "-rL",
                str(build_dir) + "/",  # ensure trailing slash for rsync
                f"{self.username}@{self.host}:{remote_dir}/",
            ],
        )

        _logger.info("Adding to IPFS")
        output = subprocess.check_output(
            ["ssh", f"{self.username}@{self.host}", "ipfs", "add", "-r", remote_dir],
            text=True,
        )
        for line in output.split("\n"):
            match = re.match(f"^added (\\w+) {remote_dir}$", line)
            if match:
                new_hash = match.group(1)
                break
        else:
            _logger.error("Couldn't find hash for blog directory!")
            return

        _logger.info("Publishing to ipns")
        subprocess.run(
            [
                "ssh",
                f"{self.username}@{self.host}",
                "ipfs",
                "name",
                "publish",
                new_hash,
            ],
        )

        # update last published
        last_published_file = self.root / "last_published"
        last_published_file.touch()
