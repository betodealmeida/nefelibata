from pathlib import Path
from typing import Any, Dict, List
import yaml

from libgravatar import Gravatar

from nefelibata import config_filename
from nefelibata.post import Post


def get_config(root: Path) -> Dict[str, Any]:
    """Return the configuration file for a weblog.
    
    Args:
      root (str): directory where the weblog lives
    """
    with open(root / config_filename) as fp:
        config = yaml.full_load(fp)

    # add gravatar as the default profile picture
    if "profile_picture" not in config["author"]:
        config["author"]["profile_picture"] = Gravatar(config["author"]["email"]).get_image()

    return config


def get_posts(root: Path) -> List[Post]:
    """Return list of posts for a given root directory.
    
    Args:
      root (str): directory where the weblog lives
    """
    config = get_config(root)
    return [Post(source, root, config) for source in (root / "posts").glob("**/*.mkd")]
