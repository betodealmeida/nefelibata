"""
An FTP publisher.
"""
import logging
from datetime import datetime
from ftplib import FTP, FTP_TLS, error_perm
from pathlib import Path

from nefelibata.publishers.base import Publisher
from nefelibata.typing import Config

_logger = logging.getLogger(__name__)


class FTPPublisher(Publisher):

    """
    A publisher that uploads the blog to an FTP server.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        root: Path,
        config: Config,
        hostname: str,
        username: str = "",
        password: str = "",
        basedir: str = "",
        use_tls: bool = False,
    ):
        super().__init__(root, config)

        self.hostname = hostname
        self.username = username
        self.password = password
        self.basedir = basedir
        self.use_tls = use_tls

    async def publish(self, force: bool = False) -> None:
        last_published_file = self.root / "last_published"
        if last_published_file.exists():
            last_published = last_published_file.stat().st_mtime
        else:
            last_published = 0

        build = self.root / "build"

        FTPClass = FTP_TLS if self.use_tls else FTP
        with FTPClass(self.hostname, self.username, self.password) as ftp:
            if self.use_tls:
                ftp.prot_p()  # pylint: disable=no-member

            if self.basedir:
                ftp.cwd(self.basedir)
            pwd = basedir = Path(ftp.pwd())

            # get files that need to be published
            since = datetime.fromtimestamp(last_published)
            modified_files = list(self.find_modified_files(force, since))

            # sort files to minimize ``CWD`` calls
            modified_files = sorted(modified_files)

            for path in modified_files:
                relative_directory = path.relative_to(build).parent
                if relative_directory != pwd.relative_to(basedir):
                    if pwd != basedir:
                        ftp.cwd(str(basedir))
                    try:
                        ftp.cwd(str(relative_directory))
                    except error_perm:
                        for directory in relative_directory.parts:
                            ftp.mkd(directory)
                            ftp.cwd(directory)
                    pwd = basedir / relative_directory

                _logger.info("Uploading %s", path)
                with open(path, "rb") as input_:
                    ftp.storbinary(f"STOR {path.name}", input_)

        # update last published
        last_published_file.touch()
