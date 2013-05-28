Nefelibata
==========

"Nefelibata" is a weblog engine that is based on these principles:

1. Published content should be on static files. If you need interaction, there's
   Javascript for that. 

2. The Unix filesystem is more than proved. Databases are an overkill for a 
   blogging platform where you write once every few hours, maximum.

3. ASCII files are important for long-term archival.

These principles led to the design where HTML pages are built from ASCII files
holding the posts using Markdown. The pages are then published to S3. There are
no servers and no databases, only static ASCII files in the filesystem.

"Nefelibata" is a portuguese word derived from "nephele" (cloud) and "batha"
(where you can walk), meaning "one who walks on clouds". Which would be an
awesome name for a blog that runs on the cloud, but this is exactly the
opposite: a blog that lives in your filesystem.
