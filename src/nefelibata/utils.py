"""
Utility functions.
"""
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Set, Type

import yaml
from pydantic import BaseModel
from rich.logging import RichHandler

from nefelibata.config import Config
from nefelibata.constants import CONFIG_FILENAME

_logger = logging.getLogger(__name__)


def setup_logging(loglevel: str) -> None:
    """
    Setup basic logging.
    """
    level = getattr(logging, loglevel.upper(), None)
    if not isinstance(level, int):
        raise ValueError(f"Invalid log level: {loglevel}")

    logformat = "[%(asctime)s] %(levelname)s: %(name)s: %(message)s"
    logging.basicConfig(
        level=level,
        format=logformat,
        datefmt="[%X]",
        handlers=[RichHandler()],
        force=True,
    )


def find_directory(cwd: Path) -> Path:
    """
    Find root of blog, starting from `cwd`.

    The function will traverse up trying to find a configuration file.
    """
    while not (cwd / CONFIG_FILENAME).exists():
        if cwd == cwd.parent:
            raise SystemExit("No configuration found!")
        cwd = cwd.parent

    return cwd


def get_config(root: Path) -> Config:
    """
    Return the configuration for a blog.
    """
    path = root / CONFIG_FILENAME
    if not path.exists():
        raise SystemExit("No configuration found!")

    with open(path, encoding="utf-8") as input_:
        config = Config(**yaml.full_load(input_))

    return config


def get_project_root() -> Path:
    """
    Return the project root.

    This is used for unit tests.
    """
    return Path(__file__).parent.parent.parent


def split_header(header: Optional[str]) -> Set[str]:
    """
    Split a comma separated list from the post header.
    """
    if header is None:
        return set()

    return {value.strip() for value in header.split(",") if value.strip()}


def load_yaml(path: Path, class_: Type[BaseModel]) -> Dict[str, BaseModel]:
    """
    Load a YAML file into a model.
    """
    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as input_:
        try:
            content = yaml.load(input_, Loader=yaml.SafeLoader)
        except (AttributeError, yaml.parser.ParserError) as ex:
            _logger.warning("Invalid YAML file: %s", path)
            raise ex

    return {name: class_(**parameters) for name, parameters in content.items()}


@contextmanager
def update_yaml(path: Path) -> Iterator[Dict[Any, Any]]:
    """
    Open or create a YAML file, and save back if modified.
    """
    if path.exists():
        with open(path, encoding="utf-8") as input_:
            original = input_.read()
            try:
                content = yaml.load(original, Loader=yaml.SafeLoader)
            except (
                AttributeError,
                yaml.parser.ParserError,
                yaml.constructor.ConstructorError,
            ) as ex:
                _logger.warning("Invalid YAML file: %s", path)
                raise ex
    else:
        original = ""
        content = {}

    try:
        yield content
    finally:
        current = yaml.dump(content)
        if current != original:
            with open(path, "w", encoding="utf-8") as output:
                output.write(current)


def dict_merge(original, update):
    """
    Recursive ``dict.update``.
    """
    for key in update:
        if (
            key in original
            and isinstance(original[key], dict)
            and isinstance(update[key], dict)
        ):
            dict_merge(original[key], update[key])
        else:
            original[key] = update[key]


def load_extra_metadata(post_directory: Path) -> Dict[str, Any]:
    """
    Load all YAML files with extra metadata for a given path.
    """
    extra_metadata = {}
    for file_path in post_directory.glob("*.yaml"):
        with open(file_path, encoding="utf-8") as input_:
            try:
                content = yaml.load(input_, Loader=yaml.SafeLoader)
            except (AttributeError, yaml.parser.ParserError):
                _logger.warning("Invalid file: %s", file_path)
                continue
        extra_metadata[file_path.stem] = content

    return extra_metadata
