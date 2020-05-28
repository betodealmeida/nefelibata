from freezegun import freeze_time
from nefelibata.assistants.mirror_images import get_resource_extension
from nefelibata.assistants.mirror_images import MirrorImagesAssistant
from requests import Response

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_mirror_images(mock_post, mocker, requests_mock):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is an external image:

        ![alt text](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 1")
        """,
        )
    post.create()

    assistant = MirrorImagesAssistant()

    mocker.patch(
        "nefelibata.assistants.mirror_images.get_resource_extension",
        return_value=".png",
    )
    requests_mock.get(
        "https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png",
        text="image-content",
    )

    assistant.process_post(post)

    with open(post.file_path.with_suffix(".html")) as fp:
        contents = fp.read()

    assert contents == (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head></head><body><p>Hi, there!</p>\n'
        "<p>This is an external image:</p>\n"
        '<p><img alt="alt text" src="img/e0e9a99aaf941ecd23bf4a3d2f0d82a2.png" title="Logo Title Text 1"/></p></body></html>'
    )

    with open(
        post.file_path.parent / "img//e0e9a99aaf941ecd23bf4a3d2f0d82a2.png",
    ) as fp:
        assert fp.read() == "image-content"


def test_mirror_images_directory_exists(mock_post, mocker, requests_mock, fs):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is an external image:

        ![alt text](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 1")
        """,
        )
    post.create()
    fs.create_dir(post.file_path.parent / "img")

    assistant = MirrorImagesAssistant()

    mocker.patch(
        "nefelibata.assistants.mirror_images.get_resource_extension",
        return_value=".png",
    )
    requests_mock.get(
        "https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png",
        text="image-content",
    )

    assistant.process_post(post)

    with open(post.file_path.with_suffix(".html")) as fp:
        contents = fp.read()

    assert contents == (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head></head><body><p>Hi, there!</p>\n'
        "<p>This is an external image:</p>\n"
        '<p><img alt="alt text" src="img/e0e9a99aaf941ecd23bf4a3d2f0d82a2.png" title="Logo Title Text 1"/></p></body></html>'
    )

    with open(
        post.file_path.parent / "img//e0e9a99aaf941ecd23bf4a3d2f0d82a2.png",
    ) as fp:
        assert fp.read() == "image-content"


def test_mirror_images_image_exists(mock_post, mocker, fs):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is an external image:

        ![alt text](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 1")
        """,
        )
    post.create()
    fs.create_file(post.file_path.parent / "img/e0e9a99aaf941ecd23bf4a3d2f0d82a2.png")

    assistant = MirrorImagesAssistant()

    mocker.patch(
        "nefelibata.assistants.mirror_images.get_resource_extension",
        return_value=".png",
    )

    assistant.process_post(post)

    with open(post.file_path.with_suffix(".html")) as fp:
        contents = fp.read()

    assert contents == (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head></head><body><p>Hi, there!</p>\n'
        "<p>This is an external image:</p>\n"
        '<p><img alt="alt text" src="img/e0e9a99aaf941ecd23bf4a3d2f0d82a2.png" title="Logo Title Text 1"/></p></body></html>'
    )


def test_get_resource_extension(requests_mock):
    requests_mock.head(
        "https://example.com/image", headers={"content-type": "image/jpeg"},
    )
    assert get_resource_extension("https://example.com/image") == ".jpg"