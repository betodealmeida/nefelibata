"""
Assistant for generating a playlist file.
"""

from pathlib import Path
from typing import Any

from nefelibata.announcers.base import Scope
from nefelibata.assistants.base import Assistant
from nefelibata.config import Config
from nefelibata.post import Post


class PlaylistAssistant(Assistant):
    """
    Assistant for generating a playlist file.
    """

    name = "playlist"
    scopes = [Scope.POST]

    def __init__(self, root: Path, config: Config, base_url: str, **kwargs: Any):
        super().__init__(root, config, **kwargs)

        self.base_url = base_url.rstrip("/")

    async def process_post(self, post: Post, force: bool = False) -> None:
        # create a playlist for each builder
        path = post.path.parent / "index.pls"
        if path.exists() and not force:
            return

        valid_enclosures = [
            enclosure for enclosure in post.enclosures if enclosure.type == "audio/mpeg"
        ]
        if not valid_enclosures:
            return

        with open(path, "w", encoding="utf-8") as output:
            output.write(
                f"""[playlist]

NumberOfEntries={len(valid_enclosures)}
Version=2

""",
            )
            for i, enclosure in enumerate(valid_enclosures):
                output.write(f"File{i+1}={self.base_url}/{enclosure.href}\n")
                output.write(f"Title{i+1}={enclosure.description}\n")
                output.write(f"Length{i+1}={enclosure.duration}\n\n")
