"""
Build the blog.
"""
import logging
import os
from pathlib import Path
from subprocess import call

from werkzeug.utils import secure_filename

from nefelibata.utils import get_config

_logger = logging.getLogger(__name__)


async def run(root: Path, title: str, type_: str = "post") -> None:
    """
    Create a new post and open editor.
    """
    _logger.info("Creating new directory")

    directory = secure_filename(title).lower()
    target = root / "posts" / directory
    if target.exists():
        raise IOError("Directory already exists!")
    target.mkdir(parents=True)

    headers = {
        "subject": title,
        "summary": "",
        "keywords": "",
    }
    if type_ != "post":
        config = get_config(root)
        try:
            extra_headers = config.templates[type_]
        except KeyError as ex:
            raise Exception(f"Invalid post type: {type_}") from ex

        headers["type"] = type_
        headers.update({f"{type_}-{key}": "" for key in extra_headers})

    filepath = target / "index.mkd"
    with open(filepath, "w", encoding="utf-8") as output:
        for key, value in headers.items():
            output.write(f"{key}: {value}\n")
        output.write("\n\n")

    editor = os.environ.get("EDITOR")
    if not editor:
        _logger.info("No EDITOR found, exiting")
        return

    call([editor, filepath])
