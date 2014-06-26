from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
import os


def mkdir_p(path):
    import errno
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

from sys import argv
try:
    if argv[1] == '-install':
        from shutil import copyfile
        src = os.path.join('cfg', 'CreateCloudMap.ini')
        dstdir = os.path.expanduser('~/.CreateCloudMap')
        dstfile = os.path.join(dstdir, 'CreateCloudMap.ini')
        updatefile = os.path.join(dstdir, 'CreateCloudMap.ini.new')
        mkdir_p(dstdir)
        if not os.path.exists(dstfile):
            copyfile(src, dstfile)
        else:
            copyfile(src, updatefile)

except IndexError:
    pass
