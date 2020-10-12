import logging
from pathlib import Path

from jinja2 import Environment
from jinja2 import FileSystemLoader
from nefelibata.builders import Builder
from nefelibata.builders import Scope
from nefelibata.post import get_posts

_logger = logging.getLogger(__name__)


class AtomBuilder(Builder):

    scopes = [Scope.SITE]

    def process_site(self, force: bool = False) -> None:
        """Generate Atom feed."""
        _logger.info("Creating Atom feed")

        env = Environment(loader=FileSystemLoader(str(self.root / "templates")))
        template = env.get_template("atom.xml")

        show = self.config.get("posts-to-show", 10)
        posts = get_posts(self.root, show)
        xml = template.render(config=self.config, posts=posts)
        with open(self.root / "build" / "atom.xml", "w") as fp:
            fp.write(xml)
