from path import path


def find_directory(cwd):
    """
    Find root directory of the blog.

    Given a path we go up the filesystem until we find the configuration file.

    """
    cwd = path(cwd)

    while not (cwd/'nefelibata.yaml').exists():
        parent = cwd/'..'
        if cwd == parent.abspath():
            raise SystemExit('No configuration found!')
        cwd = parent

    return cwd.abspath()
