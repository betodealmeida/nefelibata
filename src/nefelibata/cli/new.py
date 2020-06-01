# -*- coding: utf-8 -*-
import logging
import os
from pathlib import Path
from subprocess import call

from nefelibata import new_post
from nefelibata.utils import sanitize

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def run(root: Path, directory: str) -> None:
    """Create a new post and open editor.
    """
    logging.info("Creating new directory")
    title = directory
    directory = sanitize(directory)
    target = root / "posts" / directory
    if target.exists():
        raise IOError("Directory already exists!")
    target.mkdir()
    os.chdir(target)

    logging.info("Adding resource files")
    resources = ["css", "js", "img"]
    for resource in resources:
        (target / resource).mkdir()

    filepath = target / "index.mkd"
    with open(filepath, "w") as fp:
        fp.write(new_post.format(title=title))

    editor = os.environ.get("EDITOR")
    if not editor:
        logging.info("No EDITOR found, exiting")
        return

    call([editor, filepath])
