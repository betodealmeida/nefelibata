import os
from stat import ST_MTIME
from email.parser import Parser
from email.utils import formatdate
from xml.etree import cElementTree

import markdown

from nefelibata import find_directory


class Post(object):
    """
    Class representing a post.

    This class wraps the post, which is simply an ASCII file in email format. 
    
    """
    def __init__(self, file_path):
        self.file_path = file_path

        with open(file_path) as fp:
            self.post = Parser().parse(fp)

        self.html = markdown.markdown(self.post.get_payload(), output_format='html5')

        # add metadata
        if 'date' not in self.post:
            date = os.stat(file_path)[ST_MTIME]
            self.post['date'] = formatdate(date, localtime=True)
        if 'subject' not in self.post:
            # try to find an H1 tag or use the filename
            tree = cElementTree.fromstring('<html>%s</html>' % self.html)
            h1 = tree.find('h1')
            if h1 is not None:
                self.post['subject'] = h1.text
            else:
                self.post['subject'] = os.path.splitext(os.path.basename(file_path))[0]

        # rewrite 
        with open(file_path, 'w') as fp:
            fp.write(str(self.post))

    @property
    def date(self):
        """
        Date when the post was written.

        """
        return self.post['date']

    @property
    def updated(self):
        """
        Is the post up-to-date?

        """
        # check if the HTML version exists
        root = find_directory(os.path.dirname(self.file_path))
        build_dir = os.path.join(root, 'build')
        relative_path = self.file_path[len(root)+1:]
        relative_path = os.path.splitext(relative_path)[0] + '.html'
        html = os.path.join(build_dir, relative_path)
        if not os.path.exists(html):
            return False

        # check if file is up-to-date
        return os.stat(html)[ST_MTIME] >= os.stat(self.filepath)[ST_MTIME]

    def create(self):
        """
        Create HTML file.

        """
        print 'called on', self.file_path


def iter_posts(directory):
    """
    Return all posts from a given directory.

    """
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith(".md"):
                 yield Post(os.path.join(dirpath, filename))


if __name__ == '__main__':
    import sys
    print Post(sys.argv[1]).updated
