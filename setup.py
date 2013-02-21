from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()


version = '0.1'

install_requires = [
    # List your project dependencies here.
    # For more details, see:
    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
    'path.py>=3.0.1',
    'docopt>=0.6.1',
    'PyYAML>=3.08',
    'Markdown>=2.2.1',
    'jinja2>=2.6',
    'boto>=2.8.0',
    'twitter>=1.9.1',
    'facepy>=0.8.4',
]


setup(name='nefelibata',
    version=version,
    description="A blog engine based on data ownership and persistence",
    long_description=README + '\n\n' + NEWS,
    classifiers=[
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    keywords='blog S3 static',
    author='Roberto De Almeida',
    author_email='roberto@dealmeida.net',
    url='http://dealmeida.net/',
    license='MIT',
    packages=find_packages('src'),
    package_dir = {'': 'src'},include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    entry_points="""
        [console_scripts]
        nb = nefelibata.console:main

        [nefelibata.publisher]
        S3 = nefelibata.publisher:S3

        [nefelibata.announcer]
        twitter = nefelibata.announcer:Twitter
        facebook = nefelibata.announcer:Facebook
    """
)
