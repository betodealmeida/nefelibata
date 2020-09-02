import hashlib
import mimetypes
import re
import urllib.parse
from pathlib import Path
from typing import Tuple

import requests
from bs4 import BeautifulSoup
from mutagen.mp3 import MP3
from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.post import Post
from nefelibata.utils import modify_html
from PIL import Image


def has_valid_dimensions(path: Path) -> bool:
    im = Image.open(path)
    width, height = im.size  # type: Tuple[int, int]
    return 144 <= width <= 4096 and 144 <= height <= 4096


class TwitterCardAssistant(Assistant):

    scopes = [Scope.POST]
    container_filename = "twitter_card.html"

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
            container_path = post_directory / self.container_filename
            container_url = urllib.parse.urljoin(
                self.config["url"],
                str(container_path.relative_to(self.root / "posts")),
            )
            self._create_container(container_path, mp3_paths[0])

            card_metadata["twitter:card"] = "player"
            card_metadata["twitter:image"] = urllib.parse.urljoin(
                self.config["url"], "img/cassette.png",
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

    def _create_container(self, container_path: Path, mp3_path: Path) -> None:
        mp3 = MP3(mp3_path)

        # create container.html
        if not container_path.exists():
            with open(container_path, "w") as fp:
                fp.write("<!DOCTYPE html><html><head></head><body></body></html>")

        with modify_html(container_path) as soup:
            css = soup.head.find("link")
            if not css:
                css = soup.new_tag(
                    "link",
                    href=urllib.parse.urljoin(self.config["url"], "css/cassette.css"),
                    rel="stylesheet",
                )
                soup.head.append(css)

            audio = soup.find("audio")
            if audio:
                audio.decompose()
            audio = soup.new_tag(
                "audio",
                attrs={
                    "class": "cassette",
                    "data-album": mp3.get("TALB", "Unknown album"),
                    "data-artist": mp3.get("TPE1", "Unknown artist"),
                    "data-title": mp3.get("TIT2", mp3_path.stem),
                    "src": mp3_path.relative_to(container_path.parent),
                },
            )
            # do not append, since <script> tag should come last
            soup.body.insert(0, audio)

            js = soup.body.find("script")
            if not js:
                js = soup.new_tag(
                    "script",
                    attrs={
                        "src": urllib.parse.urljoin(
                            self.config["url"], "js/cassette.js",
                        ),
                        "async": "",
                    },
                )
                soup.body.append(js)
