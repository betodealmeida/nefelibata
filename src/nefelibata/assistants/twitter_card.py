import urllib.parse
from pathlib import Path
from typing import Tuple

import requests
from bs4 import BeautifulSoup
from mutagen.mp3 import MP3
from PIL import Image

from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.builders.twitter_card import CONTAINER_FILENAME
from nefelibata.post import Post
from nefelibata.utils import modify_html


def has_valid_dimensions(path: Path) -> bool:
    im = Image.open(path)
    width, height = im.size  # type: Tuple[int, int]
    return 144 <= width <= 4096 and 144 <= height <= 4096


class TwitterCardAssistant(Assistant):

    scopes = [Scope.POST]

    def process_post(self, post: Post, force: bool = False) -> None:
        file_path = post.file_path.with_suffix(".html")
        post_directory = post.file_path.parent

        card_metadata = {
            "twitter:card": "summary",
            "twitter:site": f'@{self.config["twitter"]["handle"]}',
            "twitter:title": "No title",
            "twitter:description": "No description",
            # "twitter:image": "",
            # "twitter:image:alt": "",
        }

        # find media in post
        mp3_paths = list(post_directory.glob("**/*.mp3"))
        jpg_paths = list(post_directory.glob("**/*.jpg"))

        # if the post has a single mp3 use a player card instead of summary
        if len(mp3_paths) == 1:
            container_path = post_directory / CONTAINER_FILENAME
            container_url = urllib.parse.urljoin(
                self.config["url"],
                str(container_path.relative_to(self.root / "posts")),
            )

            card_metadata["twitter:card"] = "player"
            card_metadata["twitter:image"] = urllib.parse.urljoin(
                self.config["url"],
                "img/cassette.png",
            )
            card_metadata["twitter:player"] = container_url
            card_metadata["twitter:player:width"] = "800"
            card_metadata["twitter:player:height"] = "464"  # 463.15

        # otherwise try to use an image
        elif jpg_paths:
            for jpg_path in jpg_paths:
                if has_valid_dimensions(jpg_path):
                    card_metadata["twitter:image"] = urllib.parse.urljoin(
                        self.config["url"],
                        str(jpg_path.relative_to(self.root / "posts")),
                    )
                    # XXX add alt
                    break

        # add meta tags
        soup: BeautifulSoup
        with modify_html(file_path) as soup:
            # collect metadata from the existing page
            for attribute in ["title", "description"]:
                meta = soup.head.find("meta", {"property": f"og:{attribute}"})
                if meta:
                    card_metadata[f"twitter:{attribute}"] = meta.attrs["content"]

            # add new meta tags with the metadata
            for name, content in card_metadata.items():
                existing = soup.head.find("meta", {"name": name})
                if existing:
                    if existing.attrs["content"] == content:
                        continue
                    else:
                        existing.decompose()

                meta = soup.new_tag("meta", attrs={"name": name, "content": content})
                soup.head.append(meta)
