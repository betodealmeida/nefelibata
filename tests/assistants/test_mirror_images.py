from datetime import datetime
from datetime import timezone
from io import BytesIO
from pathlib import Path
from typing import Any
from typing import Dict

import piexif
from freezegun import freeze_time
from nefelibata.assistants.mirror_images import get_resource_extension
from nefelibata.assistants.mirror_images import MirrorImagesAssistant
from nefelibata.builders.post import PostBuilder
from PIL import Image

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


config: Dict[str, Any] = {
    "url": "https://example.com/",
    "language": "en",
    "theme": "test-theme",
    "webmention": {"endpoint": "https://webmention.io/example.com/webmention"},
}


def test_process_post(mock_post, mocker, requests_mock):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is an external image:

        ![alt text](https://example.com/images/icon48.png "Logo Title Text 1")
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = MirrorImagesAssistant(root, config)

    mocker.patch(
        "nefelibata.assistants.mirror_images.get_resource_extension",
        return_value=".png",
    )
    requests_mock.get(
        "https://example.com/images/icon48.png", text="image-content",
    )

    assistant.process_post(post)

    with open(post.file_path.with_suffix(".html")) as fp:
        contents = fp.read()

    assert (
        contents
        == """
<!DOCTYPE html>
<html lang="en">
<head>
<meta content="article" property="og:type"/>
<meta content="Post title" property="og:title"/>
<meta content="This is the post description" property="og:description"/>
<link href="https://webmention.io/example.com/webmention" rel="webmention"/>
<link href="https://external.example.com/css/basic.css" rel="stylesheet"/>
<link href="/css/style.css" rel="stylesheet"/>
</head>
<body>
<p>Hi, there!</p>
<p>This is an external image:</p>
<p><img alt="alt text" src="img/40ae98e74569d5ca87eec869e592053d.png" title="Logo Title Text 1"/></p>
</body>
</html>"""
    )

    with open(
        post.file_path.parent / "img/40ae98e74569d5ca87eec869e592053d.png",
    ) as fp:
        assert fp.read() == "image-content"


def test_process_post_directory_exists(mock_post, mocker, requests_mock, fs):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is an external image:

        ![alt text](https://example.com/images/icon48.png "Logo Title Text 1")
        """,
        )
    PostBuilder(root, config).process_post(post)

    fs.create_dir(post.file_path.parent / "img")

    assistant = MirrorImagesAssistant(root, config)

    mocker.patch(
        "nefelibata.assistants.mirror_images.get_resource_extension",
        return_value=".png",
    )
    requests_mock.get(
        "https://example.com/images/icon48.png", text="image-content",
    )

    assistant.process_post(post)

    with open(post.file_path.with_suffix(".html")) as fp:
        contents = fp.read()

    assert (
        contents
        == """
<!DOCTYPE html>
<html lang="en">
<head>
<meta content="article" property="og:type"/>
<meta content="Post title" property="og:title"/>
<meta content="This is the post description" property="og:description"/>
<link href="https://webmention.io/example.com/webmention" rel="webmention"/>
<link href="https://external.example.com/css/basic.css" rel="stylesheet"/>
<link href="/css/style.css" rel="stylesheet"/>
</head>
<body>
<p>Hi, there!</p>
<p>This is an external image:</p>
<p><img alt="alt text" src="img/40ae98e74569d5ca87eec869e592053d.png" title="Logo Title Text 1"/></p>
</body>
</html>"""
    )

    with open(
        post.file_path.parent / "img/40ae98e74569d5ca87eec869e592053d.png",
    ) as fp:
        assert fp.read() == "image-content"


def test_process_post_image_exists(mock_post, mocker, fs):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is an external image:

        ![alt text](https://example.com/images/icon48.png "Logo Title Text 1")
        """,
        )
    PostBuilder(root, config).process_post(post)

    fs.create_file(post.file_path.parent / "img/40ae98e74569d5ca87eec869e592053d.png")

    assistant = MirrorImagesAssistant(root, config)

    mocker.patch(
        "nefelibata.assistants.mirror_images.get_resource_extension",
        return_value=".png",
    )

    assistant.process_post(post)

    with open(post.file_path.with_suffix(".html")) as fp:
        contents = fp.read()

    assert (
        contents
        == """
<!DOCTYPE html>
<html lang="en">
<head>
<meta content="article" property="og:type"/>
<meta content="Post title" property="og:title"/>
<meta content="This is the post description" property="og:description"/>
<link href="https://webmention.io/example.com/webmention" rel="webmention"/>
<link href="https://external.example.com/css/basic.css" rel="stylesheet"/>
<link href="/css/style.css" rel="stylesheet"/>
</head>
<body>
<p>Hi, there!</p>
<p>This is an external image:</p>
<p><img alt="alt text" src="img/40ae98e74569d5ca87eec869e592053d.png" title="Logo Title Text 1"/></p>
</body>
</html>"""
    )


def test_get_resource_extension(requests_mock):
    requests_mock.head(
        "https://example.com/image", headers={"content-type": "image/jpeg"},
    )
    assert get_resource_extension("https://example.com/image") == ".jpg"


def test_process_site(mock_post, mocker, requests_mock, fs):
    root = Path("/path/to/blog")

    fs.create_dir(root / "build")
    with open(root / "build/about.html", "w") as fp:
        fp.write('<img src="https://example.com/images/icon48.png" />')

    assistant = MirrorImagesAssistant(root, config)

    mocker.patch(
        "nefelibata.assistants.mirror_images.get_resource_extension",
        return_value=".png",
    )
    requests_mock.get(
        "https://example.com/images/icon48.png", text="image-content",
    )

    assistant.process_site()

    with open(root / "build/about.html") as fp:
        contents = fp.read()

    assert contents == '<img src="img/40ae98e74569d5ca87eec869e592053d.png"/>'


def test_process_post_not_modified(mock_post, mocker, requests_mock):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is an local image:

        ![alt text](icon48.png "Logo Title Text 1")
        """,
        )
        PostBuilder(root, config).process_post(post)

    assistant = MirrorImagesAssistant(root, config)

    assistant.process_post(post)

    # file shouldn't have been touched
    assert datetime.fromtimestamp(
        post.file_path.with_suffix(".html").stat().st_mtime,
    ).astimezone(timezone.utc) == datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)


def test_exif(mock_post, mocker, requests_mock):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is an external image:

        ![alt text](https://example.com/images/image.jpg "Logo Title Text 1")
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = MirrorImagesAssistant(root, config)

    mocker.patch(
        "nefelibata.assistants.mirror_images.get_resource_extension",
        return_value=".jpg",
    )

    # create 1x1 jpeg
    im = Image.new("RGB", (1, 1), color="black")
    buf = BytesIO()
    im.save(buf, format="JPEG")
    content = buf.getvalue()
    requests_mock.get(
        "https://example.com/images/image.jpg",
        content=content,
        headers={"Content-Type": "image/jpeg"},
    )

    assistant.process_post(post)

    # Image.open can take a Path, but not a fake_fs Path
    im = Image.open(
        str(post.file_path.parent / "img/dcd819cdc3ca4b41c3e83ed160c92254.jpg"),
    )
    exif = piexif.load(im.info["exif"])

    assert (
        exif["0th"][piexif.ImageIFD.ImageDescription]
        == b"https://example.com/images/image.jpg"
    )
