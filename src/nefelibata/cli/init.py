"""
Create a new blog skeleton.
"""
import logging
import os
import shutil
from pathlib import Path

from pkg_resources import resource_filename, resource_listdir

from nefelibata.builders.base import get_builders
from nefelibata.utils import get_config

_logger = logging.getLogger(__name__)


async def run(root: Path, force: bool = False) -> None:
    """
    Create a new blog skeleton.
    """
    resources = sorted(resource_listdir("nefelibata", "templates/skeleton"))
    for resource in resources:
        origin = Path(
            resource_filename(
                "nefelibata",
                os.path.join("templates/skeleton", resource),
            ),
        )
        target = root / resource
        if target.exists() and not force:
            resource_type = "Directory" if origin.is_dir() else "File"
            raise IOError(f"{resource_type} {target} already exists!")
        if origin.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            shutil.copytree(origin, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(origin, target)

    # create templates
    config = get_config(root)
    for builder in get_builders(root, config).values():
        builder.setup()

    _logger.info("Blog created!")
