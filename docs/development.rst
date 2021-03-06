Development
===========

Nefelibata is written in Python 3.9, and has been tested with Python 3.7 and 3.8 as well. It has a modularized plugin architecture, allowing new features to be easily added. Plugins are discovered through `entry points <https://packaging.python.org/specifications/entry-points/>`_, allowing anyone to write custom Python libraries that extend nefelibata.

There are 4 types of plugins:

builders
    Builders are used to generate HTML from the Markdown files. They generate the index page, tags, archives and Atom feed.
assistants
    Assistants are HTML post-processors, and run on the HTML generated by builders. They mirror images locally, save external links on the `Wayback Machine <https://archive.org/web/>`_, and more.
publishers
    Publishers will upload the static files to one or more hosting services. Currently `AWS S3 <https://aws.amazon.com/s3/>`_, `Neocities <https://neocities.org/>`_, FTP, and `IPFS <https://ipfs.io/>`_ are supported.
announcers
    Announcers will syndicate your posts externally, linking back to the post. Currently `Twitter <https://twitter.com/home>`_, `Mastodon <https://joinmastodon.org/>`_, `Medium <https://medium.com/>`_ and a few more are supported. There is also a special announcer to handle `webmentions <https://indieweb.org/Webmention-faq>`_.

Builders
--------

This is the base builder class:


.. code-block:: python

    class Builder:

        scopes: List[Scope] = []

        def __init__(self, root: Path, config: Dict[str, Any], *args: Any, **kwargs: Any):
            self.root = root
            self.config = config

        def process_post(self, post: Post, force: bool = False) -> None:
            if Scope.POST not in self.scopes:
                raise Exception(f'Scope "post" not supported by {self.__class__.__name__}')

            raise NotImplementedError("Subclasses MUST implement `process_post`")

        def process_site(self, force: bool = False) -> None:
            if Scope.SITE not in self.scopes:
                raise Exception(f'Scope "site" not supported by {self.__class__.__name__}')

            raise NotImplementedError("Subclasses MUST implement `process_site`")


A builder has one or more **scopes**, and they can be either "post" or "site". The post builder, eg, has only the "post" scope. It defines a ``process_post`` method that takes a ``Post`` object and writes an HTML file next to it.

The index builder, on the other hand, has only the "site" scope, and defines a ``process_site`` method that builds a feed from the last 10 posts. If we wanted to have a feed for comments in each post we could add the "post" scope, and add a ``process_post`` method that generates an Atom feed for each post.

Assistants
----------

Assistants are very similar to builders, and they have the exact same interface — they are a subclass of ``Builder``. The main difference is that builders work on the post Markdown, while assistants work on the generated HTML. For example, there is an assistant that extracts all links to external images, and downloads them locally.

Publishers
----------

A publisher is a class that defines a ``publish`` method. Here's a simple example:

.. code-block:: python

    from pathlib import Path
    from typing import List

    from nefelibata.publishers import Publisher


    class MyPublisher(Publisher)
        def __init__(self, root: Path, config: Dict[str, Any], secret_code: str):
            super().__init__(root, config)
            self.secret_code = secret_code

        def publish(self, force: bool = False) -> None:
            # store file with the last time weblog was published
            last_published_file = self.root / "last_published"
            if last_published_file.exists():
                last_published = last_published_file.stat().st_mtime
            else:
                last_published = 0

            modified_files: List[Path] = self.find_modified_files(force, since=last_published)
            for file in modified_files:
                pass  # upload

            # update last published
            last_published_file.touch()

To use the custom publisher users would add this to their ``nefelibata.yaml``:

.. code-block:: yaml

    publish-to:
        - my_publisher

    my_publisher:
        secret_code: 

This assumes that the publisher is exposed through an entry point:

.. code-block:: ini

    nefelibata.publisher =
        my_publisher = nefelibata.publishers.my_publisher:MyPublisher

Note that entry points are package agnostic. If you want to add a new plugin you can submit a pull request to nefelibata, but you can also create a new package declaring the entry point and nefelibata will pick it up automatically.

Announcers
----------

Announcers are responsible for two main tasks: publishing a post somewhere else, and fetching replies to it. These are performed by two methods, ``announce`` and ``collect``, respectively:

.. code-block:: python

    class MyAnnouncer(Announcer):

        id = "my_announcer"
        name = "My Announcer"
        url_header = "my-announcer-url"

        def announce(self, post: Post) -> Optional[str]:
            """Publish the post and return the URL where it was published."""
            pass

        def collect(self, post: Post) -> List[Response]:
            """Colect all responses made to the post."""
            pass


If you're interested in making your own announcer, the Mastodon announcer is a good example, since the API is straightforward. Like publishers, announcers can also take extra instantiation arguments that are defined in ``nefelibata.yaml`` and passed through the ``__init__`` method.
