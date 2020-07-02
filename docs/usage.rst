Usage
=====

Creating a new post
-------------------

Your skeleton blog already has a post called ``first/``. You can edit that post, or create a new one with the command:

.. code-block:: bash

    $ nb new "Hello, World!"

(Note that you always need to run the ``nb`` command from inside your weblog directory.)

This will create a new directory called ``hello_world/``, with the following structure:

.. code-block:: bash

    posts/hello_world/
    posts/hello_world/index.mkd
    posts/hello_world/img/
    posts/hello_world/css/
    posts/hello_world/js/

If you have the ``EDITOR`` environment set, nefelibata will automatically open your editor to edit ``index.mkd``. You can place any custom CSS, Javascript or images in the corresponding directories, or any other extra files in the ``hello_world/`` directory.

You'll notice that the ``index.mkd`` file has headers and a body. The file itself is actually stored as an email, using the `RFC 5322 format <https://tools.ietf.org/html/rfc5322.html>`_. The most important headers are:

- ``subject``: this is the title of your post.
- ``summary``: this is a one-line summary of your post.
- ``keywords``: a comma-separated list of keywords for tags.

Additionally, once the post is published a ``date`` header will be added. If the post is announced to Twitter/Mastodon/etc. a corresponding header (eg, ``mastodon-url``) will also be added.

If you want to announce your post to a custom social network you can either override the default announcers by using the ``announce-on`` header, or add an extra announcer by using the ``announce-on-extra`` header. Similarly, if you want to skip a default announcer you can use the ``announce-on-skip`` header.

Building the weblog
-------------------

To build your weblog, simply run:

.. code-block:: bash

    $ nb build

This will convert the Markdown files to HTML and build the weblog, with pages for archives and tags as well. Later, once posts have been announced to social networks, this command will also collect replies and store them locally.

Previewing the weblog
---------------------

To preview your weblog, simply run:

.. code-block:: bash

    $ nb preview

This will run an HTTP server on port 8000. Open http://localhost:8000/ on your browser so you can preview your changes.

Publishing the weblog
---------------------

Finally, you can publish your weblog with the command:

.. code-block:: bash

    $ nb publish

This will upload the weblog using any configured publishers (like S3), and announce new posts to social networks.
