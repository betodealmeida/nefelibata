==========
nefelibata
==========

A weblog engine focusing on data ownership and persistence.

How is it different?
====================

Nefelibata (Portuguese for "one who walks on clouds") focus on preserving your content. In order to achieve that goal, it works similarly to common static website generators, with the following design decisions:

- Each post is a separate directory. The actual post is written in `Markdown <https://www.markdownguide.org/>`_, and each post can have its own images, CSS, Javascript and other files. This way each post is relatively self-contained.
- Posts are converted into HTML, and the resulting weblog is composed of **only static files**. There are no databases, and all extra data is stored as JSON.
- External images are downloaded when the weblog is built, and the link is altered to point to the local resource. The engine **will warn you** if the generated HTML has any external resources (CSS, for example).
- The files are then **published** to a location using a plugin architecture (currently only S3 is supported).

All this is done with a command line utility called ``nb``.

Additionally, nefelibata recognizes that most interactions occur in social networks, like Twitter or Facebook. The engine can be configured with global or per-post **announcers**, that will post the content to social networks, so that people can comment and discuss it. When the weblog is rebuilt, the announcers will collect any replies and store them locally, so that the comments are displayed in the weblog with your post. A post can be announced to multiple social networks, and the comments will be aggregated with it.

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

If you're impatient, you can run:

.. code-block:: bash

    $ nb init blog
    $ cd blog
    $ nb build
    $ nb preview

And open http://localhost:8000/ to see your weblog. Read below for details.

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

You need to `create an S3 account <http://aws.amazon.com/s3/>`_ in order to get the AWS credentials. If you want the S3 publisher to create the bucket, configure it as a website, upload the website and configure Route 53 to point the domain name to it you need the following policy in your IAM account (replace ``blog.taoetc.org`` with your domain):

.. code-block:: json

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "s3:GetBucketWebsite",
                    "s3:PutBucketWebsite",
                    "route53:ChangeResourceRecordSets",
                    "s3:PutBucketAcl",
                    "s3:CreateBucket"
                ],
                "Resource": [
                    "arn:aws:route53:::hostedzone/taoetc.org",
                    "arn:aws:s3:::blog.taoetc.org"
                ]
            },
            {
                "Sid": "VisualEditor1",
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:PutObjectAcl"
                ],
                "Resource": "arn:aws:s3:::blog.taoetc.org/*"
            },
            {
                "Sid": "VisualEditor2",
                "Effect": "Allow",
                "Action": "route53:ListHostedZones",
                "Resource": "*"
            }
        ]
    }

This will upload your weblog to an S3 bucket and run the website from it over HTTP. If you want to serve the website over HTTPS (as I do), you need to disable Route 53 (``configure_route53`` should be empty) and `configure CloudFront <https://www.freecodecamp.org/news/simple-site-hosting-with-amazon-s3-and-https-5e78017f482a/>`_.

Finally, if you want to announce your posts on Twitter or Facebook you need to create custom applications on the respeective developer websites, and add the access tokens to the file `nefelibata.yaml`. The skeleton file has instructions on how to do this for each announcer. (There's also an announcer for `FAWM <https://fawm.org/>`_, but it's currently work in progress).

Creating a new post
-------------------

Your skeleton blog already has a post called ``first``. You can edit that post, or create a new one with the command:

.. code-block:: bash

    $ nb new "Hello, World!"

(Note that you always need to run the ``nb`` command from inside your weblog directory.)

This will create a new directory called `hello_world`, with the following structure:

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
- ``keywords``: a comma-separated list of keywords/tags/categories.

Additionally, once the post is published a ``date`` header will be added. If the psot is announced to Twitter/Facebook/etc. a corresponding header (eg, ``facebook-url``) will also be added.

If you want to announce your post to a custom social network you can either override the default announcers by using the ``announce-on`` header, or add an extra announcer by using the ``announce-on-extra`` header.

Building the weblog
-------------------

To build your webblog, simply run:

.. code-block:: bash

    $ nb build

This will convert the Markdown files to HTML and build the weblog, with pages for archives and categories as well. Later, once posts have been announced to social networks, this command will also collect replies and store them locally.

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

This will upload the weblog using any configured publisherd (like S3), and announce new posts to social networks.

What's next?
============

If you want to customize your weblog, take a look at the ``templates/`` directory inside your weblog. The templates are written in `Jinja2 <https://palletsprojects.com/p/jinja/>`_.
