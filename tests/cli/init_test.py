"""
Test ``nefelibata.cli.init``.
"""
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from nefelibata.cli import init
from nefelibata.constants import CONFIG_FILENAME


@pytest.mark.asyncio
async def test_run(
    mocker: MockerFixture,
    root: Path,
) -> None:
    """
    Test ``run``.
    """
    builder = mocker.MagicMock()
    builder.process_post = mocker.AsyncMock()
    builder.process_site = mocker.AsyncMock()

    mocker.patch("nefelibata.cli.init.get_config")
    mocker.patch("nefelibata.cli.init.get_builders", return_value={"builder": builder})

    _logger = mocker.patch("nefelibata.cli.init._logger")

    await init.run(root)

    builder.setup.assert_called()
    _logger.info.assert_called_with("Blog created!")

    assert (root / CONFIG_FILENAME).exists()
    assert (root / "posts/first/index.mkd").exists()

    # error if running again
    with pytest.raises(IOError) as excinfo:
        await init.run(root)
    assert str(excinfo.value) == "File /path/to/blog/nefelibata.yaml already exists!"

    # forcing an overwrite works, but fails for some reason with pyfakefs
    # await init.run(root, force=True)
