import os


def find_directory(cwd):
    """
    Find root directory of the blog.

    Given a path we go up the filesystem until we find the configuration file.

    """
    directory = cwd
    while not os.path.exists(os.path.join(directory, 'nefelibata.yaml')):
        parent = os.path.abspath(os.path.join(directory, '..'))
        if directory == parent:
            raise SystemExit('No configuration found!')
        directory = parent

    return directory
