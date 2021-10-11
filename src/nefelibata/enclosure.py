"""
Enclosures for media associated with posts.
"""

import mimetypes
import urllib.parse
from pathlib import Path
from typing import Dict, List, Type, Union

import piexif
from mutagen.mp3 import MP3
from pydantic import BaseModel


class Enclosure(BaseModel):
    """
    An enclosure.
    """

    path: Path
    description: str
    type: str
    length: int
    href: str


def get_pretty_duration(duration: float) -> str:
    """
    Return a nice duration from number of seconds.
    """
    units = ["h", "m", "s"]
    parts = []
    while units:
        value = int(duration) % 60 if units else duration
        parts.append((value, units.pop()))
        duration //= 60

    parts = parts[::-1]

    # remove trailing zeros
    while parts and parts[-1][0] == 0:
        parts.pop()

    # remove leading zeros
    while parts and parts[0][0] == 0:
        parts.pop(0)

    return "".join(f"{value}{unit}" for (value, unit) in parts) or "0s"


class MP3Enclosure(Enclosure):
    """
    An MP3 file.
    """

    type = "audio/mpeg"
    title: str
    artist: str
    album: str
    year: Union[int, str]
    duration: float
    track: int

    @classmethod
    def from_path(cls, root: Path, path: Path) -> "MP3Enclosure":
        """
        Build an enclosure from a path to an MP3.
        """
        length = path.stat().st_size
        href = urllib.parse.quote(str(path.relative_to(root / "posts")))

        mp3 = MP3(path)
        title = str(mp3.get("TIT2", path.stem))
        artist = str(mp3.get("TPE1", "Unknown artist"))
        album = str(mp3.get("TALB", "Unknown album"))
        year = int(str(mp3.get("TDRC", 0))) or "Unknown year"
        duration = mp3.info.length
        track = int(str(mp3.get("TRCK"))) if "TRCK" in mp3 else 0

        pretty_duration = get_pretty_duration(duration)
        description = f'"{title}" ({pretty_duration}) by {artist} ({album}, {year})'

        return cls(
            path=path,
            description=description,
            length=length,
            href=href,
            title=title,
            artist=artist,
            album=album,
            year=year,
            duration=duration,
            track=track,
        )


class ImageEnclosure(Enclosure):
    """
    An image.
    """

    path: Path
    description: str
    type: str
    length: int
    href: str

    @classmethod
    def from_path(cls, root: Path, path: Path) -> "ImageEnclosure":
        """
        Build an enclosure from a path to an image.
        """
        mimetype, _ = mimetypes.guess_type(path)
        length = path.stat().st_size
        href = urllib.parse.quote(str(path.relative_to(root / "posts")))

        if mimetype == "image/jpeg":
            exif = piexif.load(str(path))
            description = (
                exif["0th"][piexif.ImageIFD.ImageDescription] or f"Image {path.name}"
            )
        else:
            description = f"Image {path.name}"

        return cls(
            path=path,
            description=description,
            type=mimetype,
            length=length,
            href=href,
        )


mimetype_map: Dict[str, Type[Enclosure]] = {
    "audio/mpeg": MP3Enclosure,
    "image/jpeg": ImageEnclosure,
    "image/png": ImageEnclosure,
}


def get_enclosures(root: Path, post_directory: Path) -> List[Enclosure]:
    """
    Find all enclosures in a given post.
    """
    enclosures = []
    for file_path in post_directory.glob("**/*"):
        mimetype, _ = mimetypes.guess_type(file_path)
        class_ = mimetype_map.get(mimetype) if mimetype else None
        if class_:
            enclosures.append(class_.from_path(root, file_path))

    return enclosures
