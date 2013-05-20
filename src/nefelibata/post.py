# -*- coding: utf-8 -*-

from __future__ import division
import math
import os
from email.parser import Parser
from email.utils import formatdate, parsedate
import time
from datetime import datetime
from xml.etree import cElementTree

import markdown
from jinja2 import Environment, FileSystemLoader
from path import path

from nefelibata import find_directory


class Post(object):
    """
    Class representing a post.

    This class wraps the post, which is simply an ASCII file in email format. 
    
    """
    def __init__(self, file_path):
        self.file_path = path(file_path)

        # process post
        with open(file_path) as fp:
            self.post = Parser().parse(fp)
        self.html = markdown.markdown(
            self.post.get_payload(decode=True),
            extensions=['codehilite'],
            output_format='html5')

        # add metadata
        modified = False
        if 'date' not in self.post:
            date = file_path.stat().st_mtime
            self.post['date'] = formatdate(date, localtime=True)
            modified = True
        if 'subject' not in self.post:
            # try to find an H1 tag or use the filename
            tree = cElementTree.fromstring('<html>%s</html>' % self.html)
            h1 = tree.find('h1')
            if h1 is not None:
                self.post['subject'] = h1.text
            else:
                self.post['subject'] = file_path.namebase
            modified = True

        # rewrite
        if modified:
            with open(file_path, 'w') as fp:
                fp.write(str(self.post))

    @property
    def url(self):
        """
        Relative URL for the post.

        """
        root = find_directory(self.file_path.dirname())
        return (root/'posts').relpathto(self.file_path).stripext() + '.html'

    @property
    def date(self):
        """
        Date when the post was written, as datetime object.

        """
        return datetime.fromtimestamp(time.mktime(parsedate(self.post['date'])))

    @property
    def title(self):
        """
        Title of the post.

        """
        return self.post['subject']

    @property
    def summary(self):
        """
        A short summary of the post.

        """
        if self.post['summary'] is not None:
            return self.post['summary']

        # try to find an H1 tag or use the filename
        tree = cElementTree.fromstring('<html>%s</html>' % self.html)
        p = tree.find('p')
        if p is not None:
            return tree.find('p').text

        return 'No summary.'

    @property
    def updated(self):
        """
        Is the post up-to-date?

        """
        # check if the HTML version exists
        root = find_directory(self.file_path.dirname())
        relative = (root/'posts').relpathto(self.file_path)
        html = (root/'build'/relative).stripext() + '.html'
        if not html.exists():
            return False

        # check if file is up-to-date
        return html.stat().st_mtime >= self.file_path.stat().st_mtime

    def create(self, config):
        """
        Create HTML file.

        """
        # find the build directory
        origin = self.file_path.dirname()
        root = find_directory(origin)
        relative = (root/'posts').relpathto(origin)
        target = root/'build'/relative
        if not target.exists():
            target.mkdir()

        # symlink all files from origin to target
        for dir in origin.walkdirs():
            new = target/origin.relpathto(dir)
            if not new.exists():
                new.mkdir()
        for file in origin.walkfiles():
            link = target/origin.relpathto(file)
            link.remove_p()
            file.link(link)

        # find javascript and css
        scripts = [ origin.relpathto(file) for file in origin.walk('*.js') ]
        stylesheets = [ origin.relpathto(file) for file in origin.walk('*.css') ]

        # compile template
        env = Environment(loader=FileSystemLoader(os.path.join(root, 'templates')))
        template = env.get_template('post.html')
        html = template.render(
            config=config, 
            post=self, 
            breadcrumbs=[('Home', '..'), (self.title, None)],
            stylesheets=stylesheets, 
            scripts=scripts)

        filename = self.file_path.namebase + '.html'
        with open(target/filename, 'w') as fp:
            fp.write(html.encode('utf-8'))


def iter_posts(root):
    """
    Return all posts from a given directory.

    """
    for file_path in root.walk('*.md'):
        yield Post(file_path)


def create_index(root, posts, config):
    """
    Build the index.html page and archives.

    """
    env = Environment(loader=FileSystemLoader(root/'templates'))
    template = env.get_template('index.html')

    show = config.get('posts-to-show', 10)
    pages = int(math.ceil(len(posts) / show))
    previous, name = None, 'index.html'
    for page in range(pages):
        if page+1 < pages:
            next = 'archive%d.html' % (page+1)
        else:
            next = None
        html = template.render(
            config=config, 
            posts=posts[page*show:(page+1)*show],
            breadcrumbs=[('Home', None)],
            previous=previous, 
            next=next)
        with open(root/'build'/name, 'w') as fp:
            fp.write(html.encode('utf-8'))
        previous, name = name, next
