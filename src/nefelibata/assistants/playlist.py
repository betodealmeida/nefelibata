import urllib.parse
from pathlib import Path
from typing import List
from typing import TypedDict

from mutagen.mp3 import MP3
from nefelibata.assistants import Assistant
from nefelibata.assistants import Scope
from nefelibata.post import Post


class MP3Info(TypedDict):
    path: Path
    title: str
    artist: str
    album: str
    year: int
    duration: int


class PlaylistAssistant(Assistant):

    scopes = [Scope.POST]

    def process_post(self, post: Post) -> None:
        post_directory = post.file_path.parent

        mp3s: List[MP3Info] = []
        for path in post_directory.glob("**/*.mp3"):
            filename = path.relative_to(post_directory)
            mp3 = MP3(path)
            mp3s.append(
                {
                    "path": path,
                    "title": mp3.get("TIT2", filename.stem),
                    "artist": mp3.get("TPE1", "Unknown artist"),
                    "album": mp3.get("TALB", "Unknown album"),
                    "year": mp3.get("TDRC", "Unknown year"),
                    "duration": int(mp3.info.length),
                },
            )

        if not mp3s:
            return

        lines = [
            "[playlist]",
            "",
            f"NumberOfEntries={len(mp3s)}",
            "Version=2",
            "",
        ]
        for i, mp3 in enumerate(mp3s):
            relative_url = mp3["path"].relative_to(self.root / "posts")
            url = urllib.parse.urljoin(self.config["url"], str(relative_url))
            title = "{album} ({year}) - {artist} - {title}".format(**mp3)
            lines.append(f"File{i+1}={url}")
            lines.append(f"Title{i+1}={title}")
            lines.append(f'Length{i+1}={mp3["duration"]}')
            lines.append("")
        pls = "\n".join(lines).strip()

        with open(post_directory / "index.pls", "w") as fp:
            fp.write(pls)
