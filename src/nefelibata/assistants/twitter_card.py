import hashlib
import mimetypes
import re
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from mutagen.mp3 import MP3
from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.post import Post
from nefelibata.utils import modify_html


class TwitterCardAssistant(Assistant):

    scopes = [Scope.POST]
    filename = "twitter_card.html"

    def process_post(self, post: Post, force: bool = False) -> None:
        file_path = post.file_path.with_suffix(".html")

        # if this post doesn't have a single mp3, skip it
        post_directory = post.file_path.parent
        mp3_paths = list(post_directory.glob("**/*.mp3"))
        if len(mp3_paths) != 1:
            return
        mp3_path = mp3_paths[0]
        mp3 = MP3(mp3_path)

        container_path = post_directory / self.filename
        container_url = urllib.parse.urljoin(
            self.config["url"], str(container_path.relative_to(self.root / "posts")),
        )

        # tested on https://cards-dev.twitter.com/validator
        card_metadata = {
            "twitter:card": "player",
            "twitter:title": "No title",
            "twitter:description": "No description",
            "twitter:site": f'@{self.config["twitter"]["handle"]}',
            "twitter:image": urllib.parse.urljoin(
                self.config["url"], "img/cassette.png",
            ),
            "twitter:player": container_url,
            "twitter:player:width": 800,
            "twitter:player:height": 464,  # 463.15
        }

        # add meta
        soup: BeautifulSoup
        with modify_html(file_path) as soup:
            # collect metadata from the existing page
            for attribute in ["title", "description"]:
                meta = soup.head.find("meta", {"property": f"og:{attribute}"})
                if meta:
                    card_metadata[f"twitter:{attribute}"] = meta.attrs["content"]

            # add new meta tags with the metadata
            for name, content in card_metadata.items():
                if not soup.head.find("meta", {"name": name, "content": content}):
                    meta = soup.new_tag(
                        "meta", attrs={"name": name, "content": content},
                    )
                    soup.head.append(meta)

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
                    "src": mp3_path.relative_to(post.file_path.parent),
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
