=========
Changelog
=========

Version 0.3.6 - 2020-09-06
==========================

- Add missing entries for FTP publisher and 50/90 announcer in skeleton YAML
- Fix Neocities publisher so it doesn't try to POST without modified files

Version 0.3.5 - 2020-08-18
==========================

- Simplified code using context managers to parse HTML and handle JSON storage
- Renamed "categories" to "tags", in anticipation of proper categories
- Allow building and/or publishing a single post with the ``-s`` option
- When webmentions are queued, poll for their status on build
- Added announcer for 50/90 (https://fiftyninety.fawmers.org/)
- Add timeout to archive.org call
- Playlist assistant is now a builder
- Added support for Twitter cards
- Added FTP publisher

Version 0.3.4 - 2020-06-19
==========================

- Updated docs

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

- Rewrite from scratch for Python 3

Version 0.1 - 2013-02-18
========================

- Initial release
