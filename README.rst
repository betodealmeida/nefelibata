==========
nefelibata
==========

A blog engine focusing on **data ownership** and **persistence**.

How is it different?
====================

Nefelibata (Portuguese for "one who walks on clouds") is an `IndieWeb <https://indieweb.org/>`_ static website generator written in `Python <https://www.python.org/>`_ 3 that focus on preserving your content. In order to achieve that goal, it works similarly to common static website generators, with the following design decisions:

- Each post is a separate directory. The actual post is written in `Markdown <https://www.markdownguide.org/>`_ and stored as an `email message <https://tools.ietf.org/html/rfc5322.html>`_, and each post can have its own images, CSS, Javascript and other files.
- Posts are converted into HTML and/or Gemtext, and the resulting site is composed of **only static files**. There are no databases, and all extra data is stored in JSON files.
- External images are locally mirrored when the site is built, and the link is altered to point to the local resource.
- External links are saved to the `Wayback Machine <https://archive.org/web/>`_, and links are annotated with the archived link and date of archival, allowing readers to follow the original links even if they change in the future. The site and new posts are also automatically archived.
- The site can be **published** to different locations, using a plugin architecture. Currently, nefelibata supports publishing to `Amazon S3 <https://aws.amazon.com/s3/>`_, FTP, and arbitrary commands.

The IndieWeb
============

Nefelibata acknowledges that most interactions occur in social networks like Twitter or Mastodon. The engine can be configured with global or per-post **announcers** that will post to social networks linking back to the content, so that people can comment and discuss posts outside of the site, a concept called `POSSE <https://indieweb.org/POSSE>`_ (Publish on your Own Site, Syndicate Elsewhere) in the IndieWeb.

When the site is rebuilt, the announcers will collect any replies and store them locally, so that the comments are displayed in the site with your post. A post can be announced to multiple social networks, and the comments will be aggregated and preserved.

Getting started
===============

Installation
------------

First install nefelibata using a virtual environment:

.. code-block:: bash

    $ pip install nefelibata

This will add a program called ``nb`` to your path.

If you're impatient, you can run:

.. code-block:: bash

    $ nb init blog
    $ cd blog
    $ nb build

And looks at the files inside the ``build/`` directory.

Creating the site directory
-----------------------------

Once you have installed nefelibata you should initialize a directory that will hold your content:

.. code-block:: bash

    $ nb init blog
    $ ls blog
    nefelibata.yaml  nefelibata.yaml.full  posts/  templates/

Here, the file ``nefelibata.yaml`` stores the configuration for your site. The ``posts/`` directory will contain your posts, and should already have a directory called ``first/`` with an initial post. The ``templates/`` directory has the templates for generating your blog and its Atom feed, as well as a Gemini capsule. Multiple themes are supported for the HTML builder, but there's currently only one called "minimal".

Configuring your site
-----------------------

The file ``nefelibata.yaml.full`` has comments describing all the sections.

Creating a new post
-------------------

Your skeleton blog already has a post called ``first/``. You can edit that post, or create a new one with the command:

.. code-block:: bash

    $ nb new "Hello, World!"

(Note that you always need to run the ``nb`` command from inside your site directory.)

This will create a new directory called ``hello_world/``, with the following structure:

.. code-block:: bash

    posts/hello_world/
    posts/hello_world/index.mkd

If you have the ``EDITOR`` environment set, nefelibata will automatically open your editor to edit ``index.mkd``. You can place any custom CSS, Javascript or images in the corresponding directories, or any other extra files in the ``hello_world/`` directory.

You'll notice that the ``index.mkd`` file has headers and a body. The file itself is actually stored as an email, using the `RFC 5322 format <https://tools.ietf.org/html/rfc5322.html>`_. The most important headers are:

- ``subject``: this is the title of your post.
- ``summary``: this is a one-line summary of your post.
- ``keywords``: a comma-separated list of keywords/tags/tags.

Additionally, once the post is published a ``date`` header will be added.

Building the site
-------------------

To build your site, simply run:

.. code-block:: bash

    $ nb build

This will convert the Markdown files to HTML and/or Gemtext and build the site, with pages for tags and categories as well. Later, once posts have been announced to social networks, this command will also collect replies and store them locally as YAML files.

Publishing the site
---------------------

Finally, you can publish your site with the command:

.. code-block:: bash

    $ nb publish

This will upload the site using any configured publishers (like S3), and announce new posts to social networks.

What's next?
============

If you want to customize your site, take a look at the ``templates/`` directory inside your site. The templates are written in `Jinja2 <https://palletsprojects.com/p/jinja/>`_.
