from pathlib import Path
from typing import Any, Dict, Iterator
import yaml

from bs4 import BeautifulSoup
from libgravatar import Gravatar

from nefelibata import config_filename


def get_config(root: Path) -> Dict[str, Any]:
    """Return the configuration file for a weblog.
    
    Args:
      root (str): directory where the weblog lives
    """
    with open(root / config_filename) as fp:
        config = yaml.full_load(fp)

    # add gravatar as the default profile picture
    if "profile_picture" not in config["author"]:
        config["author"]["profile_picture"] = Gravatar(config["author"]["email"]).get_image()

    return config


def find_external_resources(html: str) -> Iterator[str]:
    """Find any external resources in an HTML document.
    """
    tag_attributes = [
        ("img", "src"),
        ("link", "href"),
        ("script", "src"),
    ]
    soup = BeautifulSoup(html, "html.parser")
    for tag, attr in tag_attributes:
        for el in soup.find_all(tag):
            resource = el.attrs.get(attr)
            if resource and "://" in resource:
                yield resource
