from pathlib import Path

import pytest
from nefelibata.cli.init import run

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_run(mocker, fs):

    source = Path("/path/to/source")
    fs.create_file(source / "skeleton/nefelibata.yaml")
    fs.create_dir(source / "skeleton/templates")
    fs.create_dir(source / "skeleton/posts/first")
    fs.create_file(source / "skeleton/posts/first/index.mkd")

    def mock_return_filename(package, resource_name):
        return source / resource_name

    mocker.patch(
        "nefelibata.cli.init.resource_listdir",
        return_value=["templates", "posts", "nefelibata.yaml"],
    )
    mocker.patch("nefelibata.cli.init.resource_filename", mock_return_filename)

    root = Path("/path/to/blog")
    fs.create_dir(root)
    run(root)

    assert (root / "nefelibata.yaml").exists()
    assert (root / "templates").exists()
    assert (root / "posts/first/index.mkd").exists()


def test_run_no_overwrite(mocker, fs):

    source = Path("/path/to/source")
    fs.create_file(source / "skeleton/nefelibata.yaml")
    fs.create_dir(source / "skeleton/templates")
    fs.create_dir(source / "skeleton/posts/first")
    fs.create_file(source / "skeleton/posts/first/index.mkd")

    def mock_return_filename(package, resource_name):
        return source / resource_name

    mocker.patch(
        "nefelibata.cli.init.resource_listdir",
        return_value=["templates", "posts", "nefelibata.yaml"],
    )
    mocker.patch("nefelibata.cli.init.resource_filename", mock_return_filename)

    root = Path("/path/to/blog")
    fs.create_file(root / "nefelibata.yaml")
    with pytest.raises(IOError) as excinfo:
        run(root)

    assert str(excinfo.value) == "File /path/to/blog/nefelibata.yaml already exists!"

    assert (root / "nefelibata.yaml").exists()
    assert (root / "templates").exists()
    assert (root / "posts/first/index.mkd").exists()
