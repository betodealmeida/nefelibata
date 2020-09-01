import json
import logging
from pathlib import Path

from bs4 import BeautifulSoup
from lunr import lunr
from nefelibata.builders import Builder
from nefelibata.builders import Scope
from nefelibata.post import get_posts

_logger = logging.getLogger(__name__)


class SearchBuilder(Builder):

    scopes = [Scope.SITE]

    def process_site(self, force: bool = False) -> None:
        """Generate search index
        """
        _logger.info("Creating search index")

        documents = []
        posts = get_posts(self.root)
        for post in posts:
            documents.append({
                "id": post.url,
                "title": post.title,
                "body": BeautifulSoup(post.html).text,
            })

        idx = lunr(
            ref='id',
            fields=[dict(field_name='title', boost=10), 'body'],
            documents=documents,
        )

        with open(self.root / "build/js/index.json", "w") as fp:
            json.dump(idx.serialize(), fp)
