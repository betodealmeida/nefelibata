==========
nefelibata
==========

A weblog engine focusing on data ownership and persistence.

How is it different?
====================

Nefelibata (Portuguese for "one who walks on clouds") focus on preserving your content. In order to achieve that goal, it works similarly to common static website generators, with the following design decisions:

- Each post is a separate directory. The acutal post is written in `Markdown <https://www.markdownguide.org/>`_, and each post can have its own images, CSS, Javascript and other files.
- Posts are converted into HTML, and the resulting weblog is composed of **only static files**.
- External images are downloaded when the weblog is built, and the link is altered to point to the local resource. The engine will also warn you if the generated HTML has any external resources (CSS, for example).
- The files are then **published** to a location using a plugin architecture (currently only S3 is supported).

All this is done with a command line utility called ``nb``.

Additionally, nefelibata recognizes that most interactions occur in social networks, like Twitter or Facebook. The engine can be configured with global or per-post **announcers** that post the content to social networks, so that people can comment and discuss it. When the weblog is built, the announcers will collect any replies, and store them locally, so that the comments are displayed in the weblog with your post. A post can be announced to multiple social networks, and the comments will be aggregated with it.

Getting started
===============

Installation
------------

I recommend installing nefelibata using a virtual environment:

.. code-block:: bash

    $ virtualenv -p python3 venv
    $ source venv/bin/activate
    $ pip install nefelibata

This will add a program called ``nb`` to your path.

Creating the weblog directory
-----------------------------

Once you have installed nefelibata you should initialize a directory that will hold your content:

.. code-block:: bash

    $ nb init blog
    $ ls blog
    nefelibata.yaml  posts/  templates/

Here, the file ``nefelibata.yaml`` stores the configuration for your weblog. The ```posts`` directory will contain your posts, and should have a directory called ``first``. The ``templates`` directory has the templates for generating your blog and its Atom feed. Multiple themes are supported, but there's currently only one called "pure-blog", based on `Pure.css <https://purecss.io/>`_.

Configuring your weblog
-----------------------

Open the file `nefelibata.yaml`. The first part is self-explanatory:

.. code-block:: yaml

    title: Tao etc.
    subtitle: Musings about the path and other things
    author:
        name: Beto Dealmeida
        email: roberto@dealmeida.net
    url: https://blog.taoetc.org/  # slashing trail is important
    posts-to-show: 5
    theme: pure-blog
    language: en

    # These are social icons displayed on the footer
    social:
        - title: Code
          url: "https://github.com/betodealmeida"
          icon: icon-github
        - title: Facebook
          url: "https://www.facebook.com/beto"
          icon: icon-facebook
        - title: Twitter
          url: "https://twitter.com/dealmeida"
          icon: icon-twitter

This is copied from `my weblog <https://blog.taoetc.org/>`_.

The second part defines where your weblog will be published to, and where new posts are announced:

.. code-block:: yaml

    publish-to: S3
    announce-on: twitter, facebook

In this example, the static files from the weblog will be published to an S3 bucket, and new posts will be published to both Twitter and Facebook.

The S3 section looks like this:

.. code-block:: yaml

    S3:
        AWS_ACCESS_KEY_ID:
        AWS_SECRET_ACCESS_KEY:
        bucket: blog.taoetc.org

        # Nefelibata will configure the bucket as website and also set your DNS
        # if you're using Route 53
        configure_website: true
        configure_route53: blog.taoetc.org.

