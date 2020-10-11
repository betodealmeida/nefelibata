Customization
=============

If you want to customize your weblog, take a look at the ``templates/`` directory inside your weblog. There are two different templates, ``post.html`` and ``index.html``. In the ``pure-blog`` theme both these templates extend the ``base.html`` template. The templates are written in `Jinja2 <https://palletsprojects.com/p/jinja/>`_.

As the name suggests, the ``post.html`` template is used to generate the HTML for individual posts. It defines 5 "blocks":

meta
    Metadata added to HTML head
title
    The title of the page
css
    Custom CSS used by the post
javascript
    Custom Javascript used by the post
content
    The actual HTML content of the post

You probably only need to change the last one.

The ``index.html`` template is used to generate the index page, as well as the paginated archives and tags pages, ie, any page that shows a list of posts. It defines the following blocks:

meta
    Metadata addade to the HTML head
title
    The title of the page
navigation
    Elements used to paginate the archives and the tags
content
    The actual HTML content of the posts

In the ``pure-blog`` theme the template shows only the summary of each post, and it shows the number of posts defined in the ``nefelibata.yaml`` file.

Post types
==========

You can also create mini-templates for different post types. Let's say you often review books, so you want to make a template for your reviews. Start by adding it to your ``nefelibata.yaml`` file:

.. code-block:: yaml

    templates:
        book:
            - title
            - author
            - genre
            - stars

Now, when create a new post and specify the type to be book:

.. code-block:: bash

    $ nb new -t book "An amazing book"

When you add the post, it will have extra headers on it:

.. code-block:: email 

    subject: An amazing book
    summary:
    keywords:
    type: book
    book-title:
    book-author:
    book-genre:
    book-stars:

Go on and write your post, adding the new metadata. To format the post, you now need to create the template ``templates/$theme/posts/book.html``. Here's an example:

.. code-block:: html

    <dl>
        <dt>Title</dt>
        <dd>{{ post.parsed['book-title'] }}</dd>

        <dt>Author</dt>
        <dd>{{ post.parsed['book-author'] }}</dd>

        <dt>Genre</dt>
        <dd>{{ post.parsed['book-genre'] }}</dd>

        <dt>Rating</dt>
        <dd>{{ post.parsed['book-stars'] }}</dd>
    </dl>

    {{ post.html }}

When the post is built, it will contain the rendered HTML snippet above.
