import hashlib
import re
from pathlib import Path
from typing import Any, Dict, Iterator

import requests
import yaml
from bs4 import BeautifulSoup
from libgravatar import Gravatar
from mutagen.mp3 import MP3

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

    return config


# TODO: make transform all the functions below into extensions
# that run on contexts (post, site) and that are loaded via
# entry points and enabled in the config file
# XXX: should the Atom render be an extension too?


def find_external_resources(html: str) -> Iterator[str]:
    """Find any external resources in an HTML document.
    
    Args:
      html (str): HTML document
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


def make_playlist(post: "Post") -> None:
    post_directory = post.file_path.parent

    mp3s: Dict[str, Any] = {}
    for path in post_directory.glob("**/*.mp3"):
        print(path)
        audio = MP3(path)
        print(audio.info.length)
        print(audio["TIT2"])  # title
        print(audio["TPE1"])  # artist
        print(audio["TDRC"])  # year
        print(audio["TALB"])  # album
        print(audio.keys())


if __name__ == "__main__":
    from nefelibata.post import Post

    root = Path("/home/beto/github.com/betodealmeida/blog/")
    config = get_config(root)
    post = Post(
        Path(
            "/home/beto/github.com/betodealmeida/blog/posts/100_songs_in_2019/index.mkd"
        ),
        root,
        config,
    )
    make_playlist(post)
