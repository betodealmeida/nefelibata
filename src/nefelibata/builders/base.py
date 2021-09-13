"""
Base class for builders.
"""
import logging
import shutil
from enum import Enum
from pathlib import Path
from pprint import pformat
from typing import Any, List, Optional

from jinja2 import Environment, FileSystemLoader
from pkg_resources import iter_entry_points, resource_filename, resource_listdir

from nefelibata.post import Post
from nefelibata.typing import Config

_logger = logging.getLogger(__name__)


class Scope(Enum):
    """
    The scope of a given builder.

    Builders can process a single post, the entire site, or both.
    """

    POST = "POST"
    SITE = "SITE"


class Builder:

    """
    A post builder.
    """

    name = ""
    scopes: List[Scope] = []

    def __init__(self, root: Path, config: Config, **kwargs: Any):
        self.root = root
        self.config = config
        self.kwargs = kwargs

        self.setup()

    def setup(self) -> None:
        """
        Create templates and build directory.

        This method is used to create templates required by the builder, as
        well as the directory where the build will be stored. It's called
        when the blog is first initialized (``nb init``), but also every time
        the plugin is instantiated, in case the user configures a builder
        after the blog initialization.
        """
        # create templates
        template_directory = Path("templates/builders") / self.name
        resources = resource_listdir("nefelibata", str(template_directory))
        for resource in resources:
            origin = Path(
                resource_filename("nefelibata", str(template_directory / resource)),
            )
            target = self.root / template_directory / resource
            if target.exists():
                continue
            _logger.info("Creating %s", template_directory / resource)
            if origin.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                shutil.copytree(origin, target, dirs_exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(origin, target)

        # create build directory
        build_directory = self.root / "build" / self.name
        if not build_directory.exists():
            build_directory.mkdir(parents=True)

    def get_environment(self) -> Environment:
        """
        Load a Jinja2 environment pointing to the templats.
        """
        return Environment(
            loader=FileSystemLoader(str(self.root / "templates/builders" / self.name)),
        )

    async def process_post(self, post: Post, force: bool = False) -> None:
        """
        Process a single post.
        """
        raise NotImplementedError("Subclasses MUST implement `process_post`")

    async def process_site(self, force: bool = False) -> None:
        """
        Process the entire site.
        """
        raise NotImplementedError("Subclasses MUST implement `process_site`")


def get_builders(
    root: Path,
    config: Config,
    scope: Optional[Scope] = None,
) -> List[Builder]:
    """
    Return all the builders for a given scope.
    """
    classes = {
        entry_point.name: entry_point.load()
        for entry_point in iter_entry_points("nefelibata.builder")
    }

    builders = []
    for parameters in config["builders"]:
        if "plugin" not in parameters:
            raise Exception(
                f'Invalid configuration, missing "plugin": {pformat(parameters)}',
            )
        name = parameters["plugin"]
        class_ = classes[name]
        kwargs = {k: v for k, v in parameters.items() if k != "plugin"}

        if scope in class_.scopes or scope is None:
            builders.append(class_(root, config, **kwargs))

    return builders
