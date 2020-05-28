from pathlib import Path
from typing import Any
from typing import Dict

import yaml
from libgravatar import Gravatar
from nefelibata import config_filename


def get_config(root: Path) -> Dict[str, Any]:
    """Return the configuration file for a weblog.

    Args:
      root (str): directory where the weblog lives
    """
    with open(root / config_filename) as fp:
        config: Dict[str, Any] = yaml.full_load(fp)

    # add gravatar as the default profile picture
    if "profile_picture" not in config["author"]:
        config["author"]["profile_picture"] = Gravatar(
            config["author"]["email"],
        ).get_image()

    return config
