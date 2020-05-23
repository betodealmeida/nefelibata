import hashlib
import re
from pathlib import Path
from typing import Any, Dict, Iterator
import urllib.parse

import requests
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
        config["author"]["profile_picture"] = Gravatar(
            config["author"]["email"]
        ).get_image()

    config["root"] = root

    return config


def find_external_resources(config: Dict[str, Any], filename: Path) -> Iterator[str]:
    """Find any external resources in an HTML document.
    
    Args:
      html (str): HTML document
    """
    with open(filename, "w") as fp:
        html = fp.read()

    tag_attributes = [
        ("img", "src"),
        ("link", "href"),
        ("script", "src"),
    ]
    soup = BeautifulSoup(html, "html.parser")
    for tag, attr in tag_attributes:
        for el in soup.find_all(tag):
            resource = el.attrs.get(attr)
            if (
                resource
                and "://" in resource
                and not resource.startswith(config["url"])
            ):
                yield resource
            elif resource and resource.endswith(".css"):
                yield from check_css(config, filename, resource)


def check_css(config: Dict[str, Any], filename: Path, url: str) -> Iterator[str]:
    """Find any external resources in a CSS document.

    Args:
      config: the blog configuration from nefelibata.yaml
      filename: path object to the HTML file
      url (str): URL to CSS (relative or absolute)
    """
    csspath = url_to_path(url)
    with open(csspath) as fp:
        css = fp.read()

    stylesheet = tinycss2.parse_stylesheet(
        css, skip_comments=True, skip_whitespace=True
    )
    for rule in stylesheet:
        for token in rule.contents:
            if (
                isinstance(token, tinycss2.ast.URLToken)
                and "://" in token.value
                and not token.value.startswith(config["url"])
            ):
                yield token.value


def mirror_images(html: str, mirror: Path) -> str:
    """Mirror remote images locally.
    
    Args:
      html (str): HTML document
      mirror (Path): directory where the images will be stored
    """
    # create post image directory if necessary
    if not mirror.exists():
        mirror.mkdir()

    # replace all external links
    soup = BeautifulSoup(html, "html.parser")
    for el in soup.find_all("img", src=re.compile("http")):
        # local name is a hash of the url
        url = el.attrs["src"]
        extension = Path(url).suffix
        m = hashlib.md5()
        m.update(url.encode("utf-8"))
        local = mirror / ("%s%s" % (m.hexdigest(), extension))

        # download and store locally
        if not local.exists():
            r = requests.get(url)
            with open(local, "wb") as fp:
                fp.write(r.content)

        el.attrs["src"] = "img/%s" % local.name

    return str(soup)
