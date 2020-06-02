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
        """Generate Atom feed.
        """
        _logger.info("Creating Atom feed")

        env = Environment(loader=FileSystemLoader(str(self.root / "templates")))
        template = env.get_template("atom.xml")

        posts = get_posts(self.root)
        posts.sort(key=lambda x: x.date, reverse=True)
        show = self.config.get("posts-to-show", 10)
        xml = template.render(config=self.config, posts=posts[:show])
        with open(self.root / "build" / "atom.xml", "w") as fp:
            fp.write(xml)
