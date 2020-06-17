=========
Changelog
=========

Version 0.3.3 - 2020-06-15
==========================

- Use the Rich library to colorize output from the CLI

Version 0.3.2 - 2020-06-15
==========================

- Fix rsync call in IPFS publisher that stripped the trailing slash

Version 0.3.1 - 2020-06-15
==========================

- Fix rsync call in IPFS publisher that required used to be in blog root

Version 0.3 - 2020-06-15
========================

- Clean up the codebase:
    - Improved plugin architecture with builders, assistants, publishers and announcers
    - Pre-commit hooks for mymy, flake8, black & more
    - 100% unit test coverage
- Announcers:
    - Removed Facebook announcer, since their closed API is impossible to use
    - Completed FAWM announcer
    - Added Mastodon announcer
    - Added Medium announcer
    - Added Webmention announcer
    - Added WT.Social announcer
- Assistants:
    - Moved mirror image functionality to a separate assistant
    - Moved external link warning functionality to a separate assistant
    - Added archive.org assistant
    - Added MP3 playlist assistant
    - Added assistant to make all links relative (for IPFS publishing)
- Builders:
    - Created builders for post, index, categories and Atom feed
- Publishers:
    - Added Neocities publisher
    - Added IPFS publisher

Version 0.2.1 - 2019-12-30
==========================

- Fix project URL in setup.cfg

Version 0.2 - 2019-12-30
========================

- Rewrite from scratch for Python 3.
