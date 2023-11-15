#! /usr/bin/env python2

"""
usage: %(prog)s [ -arstx ][ -# ][ -d# ]

  -a: use access time rather than mod time
  -d#: specify a maximum depth
  -r: reverse sorting order
  -s: sort by size
  -t: use total size rather than immediate size
  -x: don't cross mountpoints
  -#: show only the first # entries
"""

import os
import sys
import time
import getopt
import stat

def usage():
    opt = Options()
    print >> sys.stderr, __doc__ % opt.__dict__

class Options:
    __shared_state = {}
    def __init__(self, argv=None):
        self.__dict__ = self.__shared_state
        if argv:
            self.getopts(argv)

    def getopts(self, argv):
        self.useatime = None
        self.maxdepth = 0
        self.reverse = None
        self.bysize = None
        self.tsize = None
        self.xdev = None
        self.limit = 0

        self.prog = os.path.basename(argv[0])

        try:
            opts, self.args = getopt.getopt(argv[1:], 'ad:rstx0123456789')
        except getopt.GetoptError:
            usage()
            sys.exit(-1)
        for o, a in opts:
            if o == '-a':
                self.useatime = 1
            elif o == '-d':
                self.maxdepth = int(a)
            elif o == '-r':
                self.reverse = 1
            elif o == '-s':
                self.bysize = 1
            elif o == '-t':
                self.tsize = 1
            elif o == '-x':
                self.xdev = 1
            else: # a digit
                self.limit = 10 * self.limit + ord(o[-1]) - ord('0')

class Path:
    def __init__(self, path, parent=None):
        self.path = path
        self.parent = parent
        st = os.lstat(path)
        self.mtime = st[stat.ST_MTIME]
        self.atime = st[stat.ST_ATIME]
        self.size = self.tsize = st[stat.ST_SIZE]
        self.dev = st[stat.ST_DEV]
        mode = st[stat.ST_MODE]
        self.isdir = stat.S_ISDIR(mode)
        self.islink = stat.S_ISLNK(mode)
        self.depth = parent and parent.depth + 1 or 0

        while parent:
            parent.tsize += self.tsize
            parent = parent.parent

    def format(self, opts):
        size = humansize('%(size)4d%(sunit)s',
                         opts.tsize and self.tsize or self.size)

        tshow = opts.useatime and self.atime or self.mtime
        age = time.time() - tshow
        # if over one year old, show the year instead of hour:minute
        tfmt = age >= 31536000 and '%b %d  %Y' or '%b %d %H:%M'
        tstr = time.strftime(tfmt, time.localtime(tshow))

        path = self.path
        if path.startswith('./'):
            path = path[2:]

        if self.islink:
            what = '@'
        elif self.isdir:
            what = '/'
        else:
            what = ''

        return '%(size)s' \
               ' %(tstr)s' \
               ' - %(path)s%(what)s' % locals()

    def svalue(self, opt):
        """return the 'sort value' depending on opt"""
        if opt.bysize:
            if opt.tsize:
                rc = -self.tsize
            else:
                rc = -self.size
        elif opt.useatime:
            rc = -self.atime
        else:
            rc = -self.mtime
        if opt.reverse:
            rc *= -1
        return rc

def show(things, opt):
    if opt.maxdepth:
        key = filter(lambda x, opt=opt:
                     things[x].depth <= opt.maxdepth,
                     things.keys())
    else:
        key = things.keys()
    slist = map(lambda x, opt=opt:
                (things[x].svalue(opt), x),
                key)
    slist.sort()
    key = map(lambda x: x[1], slist)
    if opt.limit:
        for i in range(min(opt.limit, len(things))):
            print things[key[i]].format(opt)
    else:
        for i in key:
            print things[i].format(opt)

def scandir(result, dir, files):
    opt = Options()
    me = result[dir]
    for i in range(len(files) - 1, -1, -1):
        file = os.path.join(dir, files[i])
        child = Path(file, me)
        if opt.xdev and child.dev != me.dev:
            del files[i]
            continue
        result[child.path] = child

def humansize(format, size):
    """return a string that's a human readable size based on integer size"""
    sunit = 'b'
    if size > 1024:
        size /= 1024
        sunit = 'k'
    if size > 1024:
        size /= 1024
        sunit = 'M'
    if size > 1024:
        size /= 1024
        sunit = 'G'
    return format % locals()

def main(argv):
    opt = Options(argv)
    all = {}
    for path in opt.args or ['.']:
        all[path] = Path(path)
        os.path.walk(path, scandir, all)

    show(all, opt)

if __name__ == '__main__':
    main(sys.argv)
