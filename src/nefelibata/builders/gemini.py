"""
A builder for Gemini (https://gemini.circumlunar.space/).
"""
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, List

from md2gemini import md2gemini

from nefelibata.builders.base import Builder, Scope
from nefelibata.post import Post, get_posts
from nefelibata.typing import Config

_logger = logging.getLogger(__name__)


class GeminiBuilder(Builder):

    """
    A builder for the Gemini protocol.
    """

    name = "gemini"
    scopes = [Scope.POST, Scope.SITE]

    def __init__(self, root: Path, config: Config, home: str, links: str = "paragraph"):
        super().__init__(root, config)
        self.home = home.rstrip("/")
        self.links = links

        self.env = self.get_environment()

    def setup(self) -> None:
        super().setup()

        tags_directory = self.root / "build/gemini/tags"
        if not tags_directory.exists():
            tags_directory.mkdir()

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
        posts = get_posts(self.root)

        # build index and feed
        for asset in ("index.gmi", "feed.gmi"):
            path = self.root / "build/gemini" / asset
            self._build_index(path, asset, posts, force)

        # group posts by tag
        tags = defaultdict(list)
        for post in posts:
            keywords = post.metadata.get("keywords", "")
            post_tags = [keyword.strip() for keyword in keywords.split(",")]
            for tag in post_tags:
                tags[tag].append(post)
        for tag, tag_posts in tags.items():
            path = self.root / "build/gemini/tags" / (tag + ".gmi")
            self._build_index(path, "tag.gmi", tag_posts, force, tag=tag)

    def _build_index(
        self,
        path: Path,
        template_name: str,
        posts: List[Post],
        force: bool = False,
        **kwargs: Any
    ) -> None:
        """
        Build an index file from a list of posts.
        """
        last_update = path.stat().st_mtime if path.exists() else None

        if (
            last_update
            and all(post.path.stat().st_mtime < last_update for post in posts)
            and not force
        ):
            _logger.info("File %s is up-to-date, nothing to do", path)
            return

        template = self.env.get_template(template_name)
        gemini = template.render(
            config=self.config, posts=posts, home=self.home, **kwargs
        )

        _logger.info("Creating %s", path)
        with open(path, "w", encoding="utf-8") as output:
            output.write(gemini)
