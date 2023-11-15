#!/usr/local/bin/python
#
# An example CGI script to use hgweb, edit as necessary

import cgitb, os, sys
cgitb.enable()

# sys.path.insert(0, "/path/to/python/lib") # if not a system-wide install
from mercurial import hgweb

h = hgweb.hgweb("/path/to/repo", "name of repo")
h.run()
