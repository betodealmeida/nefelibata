import hashlib
import mimetypes
import re
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
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
        mp3s = list(post_directory.glob("**/*.mp3"))
        if len(mp3s) != 1:
            return
        mp3 = mp3s[0]

        container_path = post_directory / self.filename
        container_url = urllib.parse.urljoin(
            self.config["url"], str(container_path.relative_to(self.root / "posts")),
        )

        card_metadata = {
            "twitter:card": "player",
            "twitter:title": "No title",
            "twitter:description": "No description",
            "twitter:site": self.config["twitter"]["handle"],
            "twitter:image": "https://via.placeholder.com/800x464?text=Lorem%20ipsum",
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
                    print(meta)
                    soup.head.append(meta)

        # create container.html
        if not container_path.exists():
            container_path.touch()
