import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from mutagen.mp3 import MP3
from PIL import Image

from nefelibata.assistants import Scope
from nefelibata.builder import Builder
from nefelibata.post import Post
from nefelibata.utils import modify_html


CONTAINER_FILENAME = "twitter_card.html"


class TwitterCardBuilder(Builder):

    scopes = [Scope.POST]

    def process_post(self, post: Post, force: bool = False) -> None:
        post_directory = post.file_path.parent

        # find media in post
        mp3_paths = list(post_directory.glob("**/*.mp3"))

        # if the post has a single mp3 use a player card instead of summary
        if len(mp3_paths) == 1:
            container_path = post_directory / CONTAINER_FILENAME
            self._create_container(container_path, mp3_paths[0])

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
                            self.config["url"],
                            "js/cassette.js",
                        ),
                        "async": "",
                    },
                )
                soup.body.append(js)
