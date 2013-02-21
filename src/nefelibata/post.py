import os
from stat import ST_MTIME
from email.parser import Parser
from email.utils import formatdate
from xml.etree import cElementTree

import markdown
from jinja2 import Template, FileSystemLoader, Environment

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
        modified = False
        if 'date' not in self.post:
            date = os.stat(file_path)[ST_MTIME]
            self.post['date'] = formatdate(date, localtime=True)
            modified = True
        if 'subject' not in self.post:
            # try to find an H1 tag or use the filename
            tree = cElementTree.fromstring('<html>%s</html>' % self.html)
            h1 = tree.find('h1')
            if h1 is not None:
                self.post['subject'] = h1.text
            else:
                self.post['subject'] = os.path.splitext(os.path.basename(file_path))[0]
            modified = True

        # rewrite 
        if modified:
            with open(file_path, 'w') as fp:
                fp.write(str(self.post))

    @property
    def date(self):
        return self.post['date']

    @property
    def title(self):
        return self.post['subject']

    @property
    def updated(self):
        """
        Is the post up-to-date?

        """
        # check if the HTML version exists
        root = find_directory(os.path.dirname(self.file_path))
        build_dir = os.path.join(root, 'build')
        posts = os.path.join(root, 'posts')
        relative_path = self.file_path[len(posts)+1:]
        new_file = os.path.splitext(relative_path)[0] + '.html'
        html = os.path.join(build_dir, new_file)
        if not os.path.exists(html):
            return False

        # check if file is up-to-date
        return os.stat(html)[ST_MTIME] >= os.stat(self.file_path)[ST_MTIME]

    def create(self, config):
        """
        Create HTML file.

        """
        # find the build directory
        origin = os.path.dirname(self.file_path)
        root = find_directory(origin)
        posts = os.path.join(root, 'posts')
        relative_path = origin[len(posts)+1:]
        build_dir = os.path.join(root, 'build')
        target = os.path.join(build_dir, relative_path)

        # create target dir
        if not os.path.exists(target):
            os.mkdir(target)

        # symlink all files from origin to target
        for dirpath, dirnames, filenames in os.walk(origin):
            for dirname in dirnames:
                dir = os.path.join(target, dirpath[len(origin)+1:], dirname)
                if not os.path.exists(dir):
                    os.mkdir(dir)
            for filename in filenames:
                source = os.path.join(dirpath, filename)
                link_name = os.path.join(target, source[len(origin)+1:])
                if os.path.exists(link_name):
                    os.unlink(link_name)
                os.link(source, link_name)

        # find javascript and css
        scripts = []
        js = os.path.join(origin, 'js')
        if os.path.exists(js) and os.path.isdir(js):
            for file in os.listdir(js):
                if os.path.isfile(os.path.join(js, file)):
                    scripts.append('js/%s' % file)
        stylesheets = []
        css = os.path.join(origin, 'css')
        if os.path.exists(css) and os.path.isdir(css):
            for file in os.listdir(css):
                if os.path.isfile(os.path.join(css, file)):
                    stylesheets.append('css/%s' % file)

        # compile template
        env = Environment(loader=FileSystemLoader(os.path.join(root, 'templates')))
        template = env.get_template('post.html')
        html = template.render(config=config, post=self, 
                stylesheets=stylesheets, scripts=scripts)

        md_file = os.path.join(build_dir, self.file_path[len(posts)+1:])
        html_file = os.path.splitext(md_file)[0] + '.html'
        with open(html_file, 'w') as fp:
            fp.write(html)
        os.unlink(md_file)


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
