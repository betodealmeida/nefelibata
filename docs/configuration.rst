Configuration
=============

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
--------

The second part defines which parts of your weblog will be built. Unless you know what you're doing you shouldn't change anything here:

.. code-block:: yaml

    builders:
      - post
      - index
      - tags
      - atom
      - playlist

Assistants
----------

The next part defines "assistants", which are HTML post-processor that run after the builders. Assistants can mirror images locally, save external links in the `Wayback Machine <https://archive.org/web/>`_, and more:

.. code-block:: yaml

    assistants:
      - mirror_images
      - warn_external_resources
      - archive_links
      - relativize_links

Publishers
----------

The fourth part defines where your weblog will be published to once it's been built. `Neocities <https://neocities.org/>`_ is easy to setup and recommended for beginners, but you can also publish to S3, FTP, and IPFS:

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
----------

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
