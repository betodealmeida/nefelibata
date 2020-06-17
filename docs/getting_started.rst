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
