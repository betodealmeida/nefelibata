"""
An HTML builder.
"""
import logging
from pathlib import Path

import markdown

from nefelibata.builders.base import Builder, Scope
from nefelibata.typing import Config

_logger = logging.getLogger(__name__)


class HTMLBuilder(Builder):

    """
    A simple HTML builder.
    """

    name = "html"
    label = "HTML"
    extension = ".html"
    assets = ["index.html", "atom.xml"]

    scopes = [Scope.POST, Scope.SITE]

    def __init__(self, root: Path, config: Config, home: str, theme: str = "default"):
        super().__init__(root, config, home)
        self.theme = theme
        self.template_base = f"{theme}/src/"

        self.setup()

    def setup(self) -> None:
        super().setup()

        # symlink CSS
        css_directory = self.root / "templates/builders/html" / self.theme / "src/css"
        target = self.root / "build/html/css"
        if css_directory.exists() and not target.exists():
            target.symlink_to(css_directory, target_is_directory=True)

    @staticmethod
    def render(content: str) -> str:
        return markdown.markdown(
            content,
            extensions=["codehilite"],
            output_format="html",
        )
