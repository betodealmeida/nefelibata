"""
A builder for Gemini (https://gemini.circumlunar.space/).
"""
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from md2gemini import md2gemini

from nefelibata.builders.base import Builder, Scope
from nefelibata.post import Post, get_posts
from nefelibata.typing import Config

_logger = logging.getLogger(__name__)


class GeminiBuilder(Builder):

    """
    A builder for the Gemini protocol.
    """

    scopes = [Scope.POST, Scope.SITE]

    def __init__(self, root: Path, config: Config, links: str = "paragraph"):
        super().__init__(root, config)
        self.links = links

        self._create_directory()

    def _create_directory(self) -> None:
        """
        Create build directory.
        """
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

        gemini = md2gemini(post.content, links=self.links, plain=True, md_links=True)

        _logger.info("Creating Gemini post")
        with open(post_path, "w", encoding="utf-8") as output:
            output.write(gemini)

    async def process_site(self, force: bool = False) -> None:
        env = Environment(loader=FileSystemLoader(str(self.root / "templates/gemini")))
        template = env.get_template("index.gmi")
        header = template.render(config=self.config)

        index_path = self.root / "build/gemini/index.gmi"
        last_update = index_path.stat().st_mtime if index_path.exists() else None

        posts = get_posts(self.root)
        if (
            last_update
            and all(post.path.stat().st_mtime < last_update for post in posts)
            and not force
        ):
            _logger.info("Gemini index is up-to-date, nothing to do")
            return

        # add links to posts
        links = []
        for post in get_posts(self.root):
            url = post.url + ".gmi"
            links.append(f"=> {url} {post.timestamp} — {post.title}")
        gemini = header.strip() + "\n\n" + "\n".join(links)

        _logger.info("Creating Gemini index")
        with open(index_path, "w", encoding="utf-8") as output:
            output.write(gemini)
