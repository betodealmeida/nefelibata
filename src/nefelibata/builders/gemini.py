"""
A builder for Gemini (https://gemini.circumlunar.space/).
"""
import logging
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from md2gemini import md2gemini
from pkg_resources import resource_filename, resource_listdir

from nefelibata.builders.base import Builder, Scope
from nefelibata.post import Post, get_posts
from nefelibata.typing import Config

_logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path("templates/builders/gemini")


class GeminiBuilder(Builder):

    """
    A builder for the Gemini protocol.
    """

    scopes = [Scope.POST, Scope.SITE]

    def __init__(self, root: Path, config: Config, home: str, links: str = "paragraph"):
        super().__init__(root, config)
        self.home = home
        self.links = links

        self.env = Environment(loader=FileSystemLoader(str(self.root / TEMPLATE_DIR)))
        self.setup()

    def setup(self) -> None:
        """
        Create templates and build directory.
        """
        # create templates
        resources = resource_listdir("nefelibata", str(TEMPLATE_DIR))
        for resource in resources:
            origin = Path(resource_filename("nefelibata", str(TEMPLATE_DIR / resource)))
            target = self.root / TEMPLATE_DIR / resource
            if target.exists():
                continue
            _logger.info("Creating %s", TEMPLATE_DIR / resource)
            if origin.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                shutil.copytree(origin, target, dirs_exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(origin, target)

        # create build directory
        build_directory = self.root / "build/gemini"
        if not build_directory.exists():
            build_directory.mkdir(parents=True, exist_ok=True)

    async def process_post(self, post: Post, force: bool = False) -> None:
        post_path = (
            self.root
            / "build/gemini"
            / post.path.relative_to(self.root / "posts").with_suffix(".gmi")
        )
        last_update = post_path.stat().st_mtime if post_path.exists() else None

        # create directories if needed
        post_directory = post_path.parent
        if not post_directory.exists():
            post_directory.mkdir(parents=True, exist_ok=True)

        if last_update and post.path.stat().st_mtime < last_update and not force:
            _logger.info("Post %s is up-to-date, nothing to do", post_path)
            return

        content = md2gemini(post.content, links=self.links, plain=True, md_links=True)

        template = self.env.get_template("post.gmi")
        gemini = template.render(
            config=self.config,
            post=post,
            content=content,
            home=self.home,
        )

        _logger.info("Creating Gemini post")
        with open(post_path, "w", encoding="utf-8") as output:
            output.write(gemini)

    async def process_site(self, force: bool = False) -> None:
        for asset in ("index.gmi", "feed.gmi"):
            asset_path = self.root / "build/gemini" / asset
            last_update = asset_path.stat().st_mtime if asset_path.exists() else None

            posts = get_posts(self.root)
            if (
                last_update
                and all(post.path.stat().st_mtime < last_update for post in posts)
                and not force
            ):
                _logger.info("File %s is up-to-date, nothing to do", asset)
                return

            template = self.env.get_template(asset)
            gemini = template.render(config=self.config, posts=posts)

            _logger.info("Creating %s", asset)
            with open(asset_path, "w", encoding="utf-8") as output:
                output.write(gemini)
