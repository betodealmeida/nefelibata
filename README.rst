==========
nefelibata
==========

A weblog engine focusing on **data ownership** and **persistence**.

You can find the `documentation on Read the Docs <https://nefelibata.readthedocs.io/en/latest/>`_.

How is it different?
====================

Nefelibata (Portuguese for "one who walks on clouds") is an `IndieWeb <https://indieweb.org/>`_ static website generator written in `Python <https://www.python.org/>`_ 3 that focus on preserving your content. In order to achieve that goal, it works similarly to common static website generators, with the following design decisions:

- Each post is a separate directory. The actual post is written in `Markdown <https://www.markdownguide.org/>`_ and stored as an `email message <https://tools.ietf.org/html/rfc5322.html>`_, and each post can have its own images, CSS, Javascript and other files.
- Posts are converted into HTML, and the resulting weblog is composed of **only static files**. There are no databases, and all extra data is stored in JSON files.
- External images are locally mirrored when the weblog is built, and the link is altered to point to the local resource. The engine **will warn you** if the generated HTML has any external resources (CSS, for example).
- External links are saved to the `Wayback Machine <https://archive.org/web/>`_, and links are annotated with the archived link and date of archival, allowing readers to follow the original links even if they change in the future.
- The weblog can be **published** to different locations, using a plugin architecture. Currently, nefelibata supports publishing to `Amazon S3 <https://aws.amazon.com/s3/>`_, `Neocities <https://neocities.org/>`_, FTP, and `IPFS <https://ipfs.io/>`_.

The IndieWeb
============

Nefelibata acknowledges that most interactions occur in social networks like Twitter or Mastodon. The engine can be configured with global or per-post **announcers** that will post to social networks linking back to the content, so that people can comment and discuss posts outside of the weblog, a concept called `POSSE <https://indieweb.org/POSSE>`_ (Publish on your Own Site, Syndicate Elsewhere) in the IndieWeb.

When the weblog is rebuilt, the announcers will collect any replies and store them locally, so that the comments are displayed in the weblog with your post. A post can be announced to multiple social networks, and the comments will be aggregated and preserved.

Getting started
===============

Installation
------------

First install nefelibata using a virtual environment:

.. code-block:: bash

    $ python -m venv venv
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

Here, the file ``nefelibata.yaml`` stores the configuration for your weblog. The ``posts/`` directory will contain your posts, and should already have a directory called ``first/`` with an initial post. The ``templates/`` directory has the templates for generating your blog and its Atom feed. Multiple themes are supported, but there's currently only one called "pure-blog", based on `Pure.css <https://purecss.io/>`_.

Configuring your weblog
-----------------------

Open the file ``nefelibata.yaml``. The first part is self-explanatory, and you should populate with your information:

.. code-block:: yaml

    title: Example.com
    subtitle: A blog about examples
    author:
      name: John Doe
      email: john.doe@example.com
      note: This is me
    url: https://blog.example.com/  # trailing slash is important
    posts-to-show: 5
    theme: pure-blog
    language: en

    # These are social links displayed on the footer
    social:
      - title: Code
        url: "https://github.com/example"
        icon: icon-github
      - title: Facebook
        url: "https://www.facebook.com/example"
        icon: icon-facebook
      - title: Twitter
        url: "https://twitter.com/example"
        icon: icon-twitter

Builders
~~~~~~~~

The second part defines which parts of your weblog will be built. Unless you know what you're doing you shouldn't change anything here:

.. code-block:: yaml

    builders:
      - post
      - index
      - tags 
      - atom

Assistants
~~~~~~~~~~

The next part defines "assistants", which are HTML post-processor that run after the builders. Assistants can mirror images locally, save external links in the `Wayback Machine <https://archive.org/web/>`_, and more:

.. code-block:: yaml

    assistants:
      - mirror_images
      - warn_external_resources
      - playlist
      - archive_links
      - relativize_links

Publishers
~~~~~~~~~~

The fourth part defines where your weblog will be published to once it's been built. `Neocities <https://neocities.org/>`_ is easy to setup and recommended for beginners, but you can also publish to S3, FTP and IPFS:

.. code-block:: yaml

    publish-to:
      - neocities
      - S3
      - ipfs
      - ftp

Each one of the publishers has its own configuration section in the ``nefelibata.yaml`` file. For Neocities you only need your username and password:

.. code-block:: yaml

    neocities:
      username: username
      password: password
      # api_key:

After publishing for the first time, nefelibata will print out an API key that you can use instead of your username/password. Simply add it to the configuration file, and comment out the username and password fields.


The S3 section looks like this:

.. code-block:: yaml

    S3:
        AWS_ACCESS_KEY_ID:
        AWS_SECRET_ACCESS_KEY:
        bucket: blog.example.com

        # Nefelibata will configure the bucket as website and also set your DNS
        # if you're using Route 53
        configure_website: true
        configure_route53: blog.example.com.

You need to `create an S3 account <http://aws.amazon.com/s3/>`_ in order to get the AWS credentials. If you want the S3 publisher to create the bucket, configure it as a website, upload the website and configure Route 53 to point the domain name to it you need the following policy in your IAM account (replace ``blog.example.com`` with your domain):

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
                    "arn:aws:route53:::hostedzone/example.com",
                    "arn:aws:s3:::blog.example.com"
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
                "Resource": "arn:aws:s3:::blog.example.com/*"
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

The FTP publisher requires a host, and optionally a username, a password and a directory to which the content should be uploaded to:

.. code-block:: yaml

    ftp:
        host: ftp.example.com
        username: user
        password: secret
        basedir: public

In the example above, the files would be put inside the ``public`` directory. You can also specify an absolute path.

For `IPFS <https://ipfs.io/>`_ you need a host running the IPFS daemon. The ``build/`` directory will be sent to the remote host via ``rsync``, added and published to the IPFS. The config itself is simple:

.. code-block:: yaml 

    ipfs:
      username: ipfs
      host: ipfs.example.com

The weblog will be published to the `InterPlanetary Name System <https://docs.ipfs.io/concepts/ipns/>`_. If you want to give it an accessible and easy to remember name, create a text record for the subdomain ``_dnslink.blog.example.com`` with the following content:

.. code-block::

    _dnslink.blog.example.com descriptive text "dnslink=/ipns/<CID>"

Where ``CID`` is the content identifier of your host. You can read more about `DNSLink <https://docs.ipfs.io/concepts/dnslink/#publish-using-a-subdomain>`_.

Announcers
~~~~~~~~~~

Finally, the last part is used for syndicating your content. Currently nefelibata can publish to and collect replies from the following websites:

.. code-block:: yaml

    announce-on:
      - webmention
      - mastodon
      - twitter
      - wtsocial
      - medium
      - fawm

Each announcer has its own configuration section, with different requirements. The `Mastodon <https://joinmastodon.org/>`_, `Twitter <https://twitter.com/>`_ and `WT.Social <https://wt.social/>`_ announcers will publish the summary of the post, with a link back to the post in the weblog. The `Medium <https://medium.com/>`_ announcer will publish the full HTML, on the other hand.

The `Webmention <https://indieweb.org/Webmention>`_ announcer is different in that it will check all the links referenced in a post, trying to discover webmention endpoints, and sending a notification is positive. The announcer also collects mentions made to the weblog, by reading them from `Webmention.io <webmention.io>`_.

Finally, `FAWM <https://fawm.org/>`_ is a website where people try to write 14 songs during the month of February. You can only publish to FAWM during February for obvious reasons. If you like making music you should try participating!

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
- ``keywords``: a comma-separated list of keywords/tags/tags.

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

What's next?
============

If you want to customize your weblog, take a look at the ``templates/`` directory inside your weblog. The templates are written in `Jinja2 <https://palletsprojects.com/p/jinja/>`_.
