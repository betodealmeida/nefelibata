"""
An FTP publisher.
"""
import logging
from datetime import datetime, timezone
from ftplib import FTP, FTP_TLS, error_perm
from pathlib import Path
from typing import Any, Optional

from nefelibata.config import Config
from nefelibata.publishers.base import Publisher, Publishing

_logger = logging.getLogger(__name__)


class FTPPublisher(Publisher):

    """
    A publisher that uploads the blog to an FTP server.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        root: Path,
        config: Config,
        path: str,
        hostname: str,
        username: str = "",
        password: str = "",
        basedir: str = "",
        use_tls: bool = False,
        **kwargs: Any,
    ):
        super().__init__(root, config, path, **kwargs)

        self.hostname = hostname
        self.username = username
        self.password = password
        self.basedir = basedir
        self.use_tls = use_tls

    async def publish(
        self,
        since: Optional[datetime] = None,
        force: bool = False,
    ) -> Optional[Publishing]:
        build = self.root / "build" / self.path

        FTPClass = FTP_TLS if self.use_tls else FTP
        with FTPClass(self.hostname, self.username, self.password) as ftp:
            if self.use_tls:
                ftp.prot_p()  # pylint: disable=no-member

            if self.basedir:
                ftp.cwd(self.basedir)
            pwd = basedir = Path(ftp.pwd())

            # get files that need to be published, sorted to minimize ``CWD`` calls
            modified_files = sorted(self.find_modified_files(force, since))

            for path in modified_files:
                relative_directory = path.relative_to(build).parent
                if relative_directory != pwd.relative_to(basedir):
                    if pwd != basedir:
                        ftp.cwd(str(basedir))
                    for directory in relative_directory.parts:
                        try:
                            ftp.cwd(directory)
                        except error_perm:
                            ftp.mkd(directory)
                            ftp.cwd(directory)
                    pwd = basedir / relative_directory

                _logger.info("Uploading %s", path)
                with open(path, "rb") as input_:
                    ftp.storbinary(f"STOR {path.name}", input_)

        if modified_files:
            return Publishing(timestamp=datetime.now(timezone.utc))

        return None
