"""Module for working with posts.

This module defines a post class and helper functions for working with posts.

"""
# -*- coding: utf-8 -*-

from __future__ import division
import re
import math
from email.parser import Parser
from email.utils import formatdate, parsedate
import time
from datetime import datetime
from lxml import etree
import md5

import markdown
from jinja2 import Environment, FileSystemLoader
from path import path
from simplejson import load
import dateutil.parser
import requests
from bs4 import BeautifulSoup

from nefelibata import find_directory


class Post(object):

    """
    Class representing a post.

    This class wraps the post, which is simply an ASCII file in email format.

    """

    def __init__(self, file_path):
        """Post representation."""
        self.file_path = path(file_path)

        # process post
        with open(file_path) as fp:
            self.post = Parser().parse(fp)
        self.raw = self.post.get_payload(decode=True).decode('utf-8')
        self.html = markdown.markdown(
            self.raw,
            extensions=['codehilite'],
            output_format='html5')

        # add metadata
        modified = False
        if 'date' not in self.post:
            date = self.file_path.stat().st_mtime
            self.post['date'] = formatdate(date, localtime=True)
            modified = True
        if 'subject' not in self.post:
            # try to find an H1 tag or use the filename
            parser = etree.HTMLParser()
            tree = etree.fromstring(self.html, parser)
            h1 = tree.xpath('//h1')
            if h1:
                self.post['subject'] = h1[0].text
            else:
                self.post['subject'] = self.file_path.namebase
            modified = True

        # rewrite
        if modified:
            self.save()

    def save(self):
        """Save back a post, after modifying it."""
        with open(self.file_path, 'w') as fp:
            fp.write(str(self.post))

    @property
    def parsed(self):
        """Parsed representation of the post."""
        parser = etree.HTMLParser()
        return etree.fromstring(self.html, parser)

    @property
    def url(self):
        """Relative URL for the post."""
        root = find_directory(self.file_path.dirname())
        return (root/'posts').relpathto(self.file_path).stripext() + '.html'

    @property
    def date(self):
        """Date when the post was written, as datetime object."""
        return datetime.fromtimestamp(
            time.mktime(parsedate(self.post['date'])))

    @property
    def title(self):
        """Title of the post."""
        return self.post['subject']

    @property
    def summary(self):
        """A short summary of the post."""
        if self.post['summary'] is not None:
            return self.post['summary']

        # try to find an H1 tag or use the filename
        parser = etree.HTMLParser()
        tree = etree.fromstring(self.html, parser)
        p = tree.xpath("//p")
        if p:
            summary = ''.join(p[0].itertext())
            if len(summary) > 140:
                summary = summary[:140] + '&#8230;'
            return summary

        return 'No summary.'

    @property
    def updated(self):
        """Return true if the post up-to-date."""
        # check if the HTML version exists
        root = find_directory(self.file_path.dirname())
        relative = (root/'posts').relpathto(self.file_path)
        html = (root/'build'/relative).stripext() + '.html'
        if not html.exists():
            return False

        # check if file is up-to-date
        return html.stat().st_mtime >= self.file_path.stat().st_mtime

    def create(self, config):
        """Create HTML file."""
        # find the build directory
        origin = self.file_path.dirname()
        root = find_directory(origin)
        relative = (root/'posts').relpathto(origin)
        target = root/'build'/relative
        if not target.exists():
            target.mkdir()

        # find javascript and css
        scripts = [target.relpathto(file) for file in target.walk('*.js')]
        scripts.sort()
        stylesheets = [target.relpathto(file) for file in target.walk('*.css')]

        # load json files into the scope
        json = {}
        for file in origin.walk('*.json'):
            with open(file) as fp:
                json[file.namebase] = load(fp)

        # compile template
        env = Environment(
            loader=FileSystemLoader(root/'templates'/config['theme']))
        env.filters['formatdate'] = jinja2_formatdate
        template = env.get_template('post.html')
        html = template.render(
            config=config,
            post=self,
            breadcrumbs=[('Home', '..'), (self.title, None)],
            stylesheets=stylesheets,
            scripts=scripts,
            json=json)

        # make local copies of external images
        html = mirror_images(html, origin/'img')

        # symlink all files from origin to target
        for dir in origin.walkdirs():
            new = target/origin.relpathto(dir)
            if not new.exists():
                new.mkdir()
        for file in origin.walkfiles():
            link = target/origin.relpathto(file)
            link.remove_p()
            file.link(link)

        filename = self.file_path.namebase + '.html'
        with open(target/filename, 'w') as fp:
            fp.write(html.encode('utf-8'))


def mirror_images(html, mirror):
    """Mirror remote images locally."""
    # create post image directory if necessary
    if not mirror.exists():
        mirror.mkdir()

    # replace all external links
    soup = BeautifulSoup(html)
    for el in soup.find_all('img', src=re.compile("http")):
        # local name is a hash of the url
        url = el.attrs['src']
        extension = path(url).ext
        m = md5.new()
        m.update(url)
        local = mirror/('%s%s' % (m.hexdigest(), extension))

        # download and store locally
        if not local.exists():
            r = requests.get(url)
            with open(local, 'w') as fp:
                fp.write(r.content)

        el.attrs['src'] = 'img/%s' % local.name

    return unicode(soup)


def jinja2_formatdate(obj, fmt):
    """Jinja filter for formatting dates."""
    if isinstance(obj, basestring):
        obj = dateutil.parser.parse(obj)
    return obj.strftime(fmt)


def iter_posts(root):
    """Return all posts from a given directory."""
    for file_path in root.walk('*.mkd'):
        yield Post(file_path)


def create_index(root, posts, config):
    """Build the index.html page and archives."""
    env = Environment(
        loader=FileSystemLoader(root/'templates'/config['theme']))
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


def create_feed(root, posts, config):
    """Build Atom feed."""
    env = Environment(
        loader=FileSystemLoader(root/'templates'))
    template = env.get_template('atom.xml')

    show = config.get('posts-to-show', 10)
    xml = template.render(
        config=config,
        posts=posts,
        show=show)
    with open(root/'build/atom.xml', 'w') as fp:
        fp.write(xml.encode('utf-8'))
