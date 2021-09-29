"""
Base class for builders.
"""
import logging
import shutil
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader
from pkg_resources import iter_entry_points, resource_filename, resource_listdir

from nefelibata import __version__
from nefelibata.post import Post, get_posts
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

    # The name of the builder; this should match the name of the entry point.
    name = ""

    # A display name for the builder, eg, "Gemini".
    label = ""

    # The default extension of the templates and the generated files, including
    # the period (if any).
    extension = ""

    # The directory where the templates live inside ``templates/builders/{name}/``.
    template_base = ""

    # A list of templates that should be processed when building the site.
    site_templates: List[str] = []

    # The scopes in which the builder should run, either processing a single post
    # (``Scope.POST``), processing the whole site (``Scope.SITE``), or both.
    scopes: List[Scope] = []

    def __init__(
        self, root: Path, config: Config, home: str, path: str = "", **kwargs: Any
    ):
        self.root = root
        self.config = config
        self.path = path or self.name
        self.home = home.rstrip("/")
        self.kwargs = kwargs

        self.env = self.get_environment()

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

        # create build directories
        build_directory = self.root / "build" / self.path
        if not build_directory.exists():
            build_directory.mkdir(parents=True)

        tags_directory = self.root / "build" / self.path / "tags"
        if not tags_directory.exists():
            tags_directory.mkdir()

        categories_directory = self.root / "build" / self.path / "categories"
        if not categories_directory.exists():
            categories_directory.mkdir()

    def absolute_uri(self, post: Post) -> str:
        """
        Return the absolute URI for a post.
        """
        return f"{self.home}/{post.url}{self.extension}"

    @staticmethod
    def render(content: str) -> str:
        """
        Render the post content.
        """
        return content

    def get_environment(self) -> Environment:
        """
        Load a Jinja2 environment pointing to the templats.
        """
        return Environment(
            loader=FileSystemLoader(str(self.root / "templates/builders" / self.name)),
            lstrip_blocks=True,
            trim_blocks=True,
        )

    async def process_post(self, post: Post, force: bool = False) -> None:
        """
        Process a single post.
        """
        post_path = (
            self.root
            / "build"
            / self.path
            / post.path.relative_to(self.root / "posts").with_suffix(self.extension)
        )
        last_update = post_path.stat().st_mtime if post_path.exists() else None

        # create directories if needed
        post_directory = post_path.parent
        if not post_directory.exists():
            post_directory.mkdir(parents=True, exist_ok=True)

        if last_update and post.path.stat().st_mtime < last_update and not force:
            _logger.info("Post %s is up-to-date, nothing to do", post_path)
            return

        template = self.env.get_template(
            f"{self.template_base}{post.type}{self.extension}",
        )
        content = template.render(
            config=self.config,
            post=post,
            home=self.home,
            render=self.render,
            __version__=__version__,
            sorted=sorted,
        )

        _logger.info("Creating %s post", self.label)
        with open(post_path, "w", encoding="utf-8") as output:
            output.write(content)

    async def process_site(self, force: bool = False) -> None:
        """
        Process the entire site.
        """
        posts = get_posts(self.root, self.config)

        # build index and feed
        for asset in self.site_templates:
            path = self.root / "build" / self.path / asset
            template_name = f"{self.template_base}{asset}"
            self._build_index(path, template_name, posts, force)

        # template for groups (tags and categories)
        template_name = f"{self.template_base}group{self.extension}"

        # group posts by tag
        tags = defaultdict(list)
        for post in posts:
            for tag in sorted(post.tags):
                tags[tag].append(post)
        for tag, tag_posts in tags.items():
            path = self.root / "build" / self.path / "tags" / (tag + self.extension)
            self._build_index(path, template_name, tag_posts, force, title=tag)

        # group tags by categories
        categories = defaultdict(list)
        for post in posts:
            for category in sorted(post.categories):
                categories[category].append(post)
        for category, category_posts in categories.items():
            path = (
                self.root
                / "build"
                / self.path
                / "categories"
                / (category + self.extension)
            )
            title = self.config["categories"][category]["label"]
            subtitle = self.config["categories"][category]["description"]
            self._build_index(
                path,
                template_name,
                category_posts,
                force,
                title=title,
                subtitle=subtitle,
            )

    def _build_index(
        self,
        path: Path,
        template_name: str,
        posts: List[Post],
        force: bool = False,
        **kwargs: Any,
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
        content = template.render(
            config=self.config,
            posts=posts,
            home=self.home,
            __version__=__version__,
            render=self.render,
            sorted=sorted,
            **kwargs,
        )

        _logger.info("Creating %s", path)
        with open(path, "w", encoding="utf-8") as output:
            output.write(content)


def get_builders(
    root: Path,
    config: Config,
    scope: Optional[Scope] = None,
) -> Dict[str, Builder]:
    """
    Return all the builders for a given scope.
    """
    classes = {
        entry_point.name: entry_point.load()
        for entry_point in iter_entry_points("nefelibata.builder")
    }

    builders = {}
    for name, parameters in config["builders"].items():
        plugin = parameters["plugin"]
        class_ = classes[plugin]

        if scope is None or scope in class_.scopes:
            builders[name] = class_(root, config, **parameters)

    return builders
