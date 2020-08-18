==========
nefelibata
==========

A weblog engine focusing on **data ownership** and **persistence**.

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

Contents
========

.. toctree::
   :maxdepth: 2

   Getting Started <getting_started>
   Configuration <configuration>
   Usage <usage>
   Customization <customization>
   Development <development>
   License <license>
   Authors <authors>
   Changelog <changelog>
   Module Reference <api/modules>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _toctree: http://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html
.. _reStructuredText: http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _references: http://www.sphinx-doc.org/en/stable/markup/inline.html
.. _Python domain syntax: http://sphinx-doc.org/domains.html#the-python-domain
.. _Sphinx: http://www.sphinx-doc.org/
.. _Python: http://docs.python.org/
.. _Numpy: http://docs.scipy.org/doc/numpy
.. _SciPy: http://docs.scipy.org/doc/scipy/reference/
.. _matplotlib: https://matplotlib.org/contents.html#
.. _Pandas: http://pandas.pydata.org/pandas-docs/stable
.. _Scikit-Learn: http://scikit-learn.org/stable
.. _autodoc: http://www.sphinx-doc.org/en/stable/ext/autodoc.html
.. _Google style: https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
.. _NumPy style: https://numpydoc.readthedocs.io/en/latest/format.html
.. _classical style: http://www.sphinx-doc.org/en/stable/domains.html#info-field-lists
