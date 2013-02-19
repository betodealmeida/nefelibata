"""
Nefelibata blog engine.

Usage:
  nb init [DIRECTORY]
  nb build [DIRECTORY]
  nb publish [DIRECTORY]

Actions:
  init          Create a new blog skeleton.
  build         Build blog HTML files.
  publish       Publish blog to configured locations and announce new posts.

Options:
  -h --help     Show this screen.
  --version     Show version.

Released under the MIT license.
(c) 2013 Roberto De Almeida <roberto@dealmeida.net>

"""

import os
import shutil
from pkg_resources import resource_listdir, resource_filename


def init(directory):
    """
    Create the basic structure copying from skeleton.

    By default, we create the blog in the current directory.

    """
    if directory is None:
        directory = '.'

    # list all resources in the skeleton directory
    resources = resource_listdir('nefelibata', 'skeleton')

    # and extract them to our target
    for resource in resources:
        origin = resource_filename('nefelibata', os.path.join('skeleton', resource))
        target = os.path.join(directory, resource)
        if os.path.isdir(origin):
            shutil.copytree(origin, target)
        else:
            shutil.copy(origin, target)

    print 'Blog created!'


def build(directory):
    """
    Build all static pages from posts.

    If no directory is specified we go up until we find a configuration file.

    """
    if directory is None:
        directory = os.getcwd()
        while not os.path.exists(os.path.join(directory, 'nefelibata.yaml')):
            directory = os.path.abspath(os.path.join(directory, '..'))
            if directory == '/':
                raise SystemExit('No configuration found!')
    posts = os.path.join(directory, 'posts')

    # check all files that need to be processed


def publish(target):
    """
    Publish the blog to the defined storages.

    """
    pass


def main():
    from docopt import docopt

    arguments = docopt(__doc__)
    if arguments['init']:
        init(arguments['DIRECTORY'])
    elif arguments['build']:
        build(arguments['DIRECTORY'])
    elif arguments['publish']:
        publish(arguments['DIRECTORY'])


if __name__ == '__main__':
    main()
