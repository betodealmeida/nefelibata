"""
An HTML builder.
"""
import logging
from pathlib import Path
from typing import Any

import marko

from nefelibata.builders.base import Builder
from nefelibata.config import Config

_logger = logging.getLogger(__name__)


class HTMLBuilder(Builder):

    """
    A simple HTML builder.
    """

    name = "html"
    label = "HTML"
    extension = ".html"
    site_templates = ["index.html", "atom.xml"]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        root: Path,
        config: Config,
        home: str,
        path: str = "",
        theme: str = "minimal",
        **kwargs: Any,
    ):
        super().__init__(root, config, home, path, **kwargs)
        self.theme = theme
        self.template_base = f"{theme}/src/"

    def setup(self) -> None:
        super().setup()

        # symlink CSS
        css_directory = self.root / "templates/builders/html" / self.theme / "src/css"
        target = self.root / "build" / self.path / "css"
        if css_directory.exists() and not target.exists():
            target.symlink_to(css_directory, target_is_directory=True)

    @staticmethod
    def render(content: str) -> str:
        markdown = marko.Markdown(extensions=["codehilite"])
        return markdown.convert(content)
