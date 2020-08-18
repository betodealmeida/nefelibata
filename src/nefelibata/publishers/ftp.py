import logging
import mimetypes
from ftplib import FTP
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import requests
from nefelibata.publishers import Publisher

_logger = logging.getLogger(__name__)


class FTPPublisher(Publisher):

    """A publisher that uploads the weblog to FTP."""

    def __init__(
        self,
        root: Path,
        config: Dict[str, Any],
        host: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        basedir: Optional[str] = None,
    ):
        super().__init__(root, config)

        self.host = host
        self.username = username or ""
        self.password = password or ""
        self.basedir = basedir

    def publish(self, force: bool = False) -> None:
        # store file with the last time weblog was published
        last_published_file = self.root / "last_published"
        if last_published_file.exists():
            last_published = last_published_file.stat().st_mtime
        else:
            last_published = 0

        build = self.root / "build"
        with FTP(self.host, self.username, self.password) as ftp:
            if self.basedir:
                ftp.cwd(self.basedir)
            pwd = basedir = Path(ftp.pwd())

            # sort files to prevent unneeded calls to CWD
            modified_files = sorted(self.find_modified_files(force, last_published))
            for path in modified_files:
                relative_directory = path.relative_to(build).parent
                if relative_directory != pwd.relative_to(basedir):
                    if pwd != basedir:
                        ftp.cwd(str(basedir))
                    for directory in relative_directory.parts:
                        try:
                            ftp.cwd(directory)
                        except Exception:
                            ftp.mkd(directory)
                            ftp.cwd(directory)
                    pwd = basedir / relative_directory

                with open(path, "rb") as fp:
                    ftp.storbinary(f"STOR {path.name}", fp)

        # update last published
        last_published_file.touch()
