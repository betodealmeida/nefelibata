"""
A publisher that calls external commands.
"""
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from nefelibata.config import Config
from nefelibata.publishers.base import Publisher, Publishing

_logger = logging.getLogger(__name__)


class CommandPublisher(Publisher):

    """
    A publisher that calls external commands.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        root: Path,
        config: Config,
        path: str,
        post_commands: List[str],
        site_commands: List[str],
        **kwargs: Any,
    ):
        super().__init__(root, config, path, **kwargs)

        self.post_commands = post_commands
        self.site_commands = site_commands

    async def publish(
        self,
        since: Optional[datetime] = None,
        force: bool = False,
    ) -> Optional[Publishing]:
        build = self.root / "build" / self.path

        modified_files = list(self.find_modified_files(force, since))
        if not modified_files:
            return None

        os.chdir(build)
        for path in modified_files:
            for command in self.post_commands:
                _logger.info("Running command %s on file %s", command, path)
                subprocess.run(
                    command,
                    shell=True,
                    check=True,
                    env={"path": path.relative_to(build)},
                )

        for command in self.site_commands:
            _logger.info("Running command %s", command)
            subprocess.run(command, shell=True, check=True)

        return Publishing(timestamp=datetime.now(timezone.utc))
