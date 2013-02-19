class Post(object):
    def __init__(self, filepath):
        self.filepath = filepath

    @property
    def date(self):
        """
        Date when the post was written.

        """
        pass

    @property
    def updated(self):
        """
        Is the post up-to-date?

        """
        pass

    def create(self):
        """
        Create HTML file.

        """
        pass


def iter_posts(directory):
    """
    Return all posts from a given directory.

    """
    pass
