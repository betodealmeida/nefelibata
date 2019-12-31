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

WIP
