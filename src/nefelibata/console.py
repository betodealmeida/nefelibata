# -*- coding: utf-8 -*-

"""
Nefelibata blog engine.

Usage:
  nb init [DIRECTORY]
  nb build [DIRECTORY]
  nb preview [-p PORT] [DIRECTORY]
  nb publish [DIRECTORY]

Actions:
  init          Create a new blog skeleton.
  build         Build blog HTML files.
  preview       Runs SimpleHTTPServer and opens the browser.
  publish       Publish blog to configured locations and announce new posts.

Options:
  -h --help     Show this screen.
  --version     Show version.
  -p PORT       Port to run the web server for preview. [default: 8000]

Released under the MIT license.
(c) 2013 Roberto De Almeida <roberto@dealmeida.net>

"""

import os
from pkg_resources import resource_listdir, resource_filename, iter_entry_points
import SimpleHTTPServer
import SocketServer
import webbrowser

import yaml
from path import path

from nefelibata import find_directory
from nefelibata.post import iter_posts, create_index


def init(root):
    """
    Create the basic structure copying from skeleton.

    By default, we create the blog in the current directory.

    """
    # list all resources in the skeleton directory
    resources = resource_listdir('nefelibata', 'skeleton')

    # and extract them to our target
    for resource in resources:
        origin = path(resource_filename('nefelibata',
            os.path.join('skeleton', resource)))
        target = root/resource
        # good guy Greg does not overwrite existing files
        if target.exists():
            raise IOError('File already exists!')
        if origin.isdir():
            origin.copytree(target)
        else:
            origin.copy(target)

    print 'Blog created!'


def build(root):
    """
    Build all static pages from posts.

    """
    # load configuration
    with open(root/'nefelibata.yaml') as fp:
        config = yaml.load(fp)

    # create build directory if necessary and copy css/js
    build = root/'build'
    if not build.exists():
        build.mkdir()
        (build/'css').mkdir()
        (build/'js').mkdir()
        (build/'img').mkdir()

    # sync stylesheets and scripts
    css = root/'templates/css'
    for stylesheet in css.files():
        (css/stylesheet).copy(build/'css')
    js = root/'templates/js'
    for script in js.files():
        (js/script).copy(build/'js')
    imgs = root/'templates/img'
    for img in imgs.files():
        (imgs/img).copy(build/'img')

    # load announcers to collect interactions
    announcers = {
        a.name: a.load() for a in iter_entry_points('nefelibata.announcer')
    }
    names = config['announce-on'] or []
    if isinstance(names, basestring):
        names = [names]

    # check all files that need to be processed
    posts = list(iter_posts(root/'posts'))
    posts.sort(key=lambda x: x.date, reverse=True)
    for post in posts:
        for name in names:
            section = config[name]
            announcer = announcers[name](post, **section)
            announcer.collect()

        # create HTML 
        if not post.updated:
            post.create(config)

    # build the index
    create_index(root, posts, config)

    print 'Blog built!'


def preview(root, port=8000):
    build = root/'build'
    os.chdir(build)

    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("", port), Handler)
    print "serving at port %s" % port
    webbrowser.open("http://localhost:%d/" % port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print "exiting..."
        httpd.shutdown()


def publish(root):
    """
    Publish the blog to the defined storages.

    """
    # load configuration
    with open(root/'nefelibata.yaml') as fp:
        config = yaml.load(fp)

    # load publishers
    publishers = {
        p.name: p.load() for p in iter_entry_points('nefelibata.publisher')
    }

    # publish site
    names = config['publish-to'] or []
    if isinstance(names, basestring):
        names = [names]
    for name in names:
        section = config[name]
        publisher = publishers[name](**section)
        publisher.publish(root/'build')

    # load announcers
    announcers = {
        a.name: a.load() for a in iter_entry_points('nefelibata.announcer')
    }

    # announce them
    posts = list(iter_posts(root/'posts'))
    posts.sort(key=lambda x: x.date, reverse=True)
    for post in posts:
        names = post.post.get('announce-on', config['announce-on']) or []
        if isinstance(names, basestring):
            names = [names]
        for name in names:
            section = config[name]
            announcer = announcers[name](post, **section)
            announcer.announce()


def main():
    from docopt import docopt

    arguments = docopt(__doc__)

    # Get the directory from our blog. If not defined we assume we're 
    # inside the blog, so we may need to go up the filesystem in order to find
    # the root.
    if arguments['DIRECTORY'] is None:
        root = find_directory(os.getcwd())
    else:
        root = path(arguments['DIRECTORY'])

    if arguments['init']:
        init(root)
    elif arguments['build']:
        build(root)
    elif arguments['preview']:
        preview(root, int(arguments['-p']))
    elif arguments['publish']:
        publish(root)


if __name__ == '__main__':
    main()
