from __future__ import print_function
# from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
from setuptools import setup

from setuptools.command.install import install as _install
import os
import versioneer
import datetime
from pathlib import Path


def copy_config():
    from shutil import copyfile, move
    srcfiles = [
        'CreateCloudMap.ini',
    ]
    srcfiles_overwrite = [
    ]

    dstdir = os.path.expanduser('~/.CreateCloudMap')
    Path(dstdir).mkdir(parents=True, exist_ok=True)

    for src in srcfiles:
        dstfile = os.path.join(dstdir, src)
        srcpath = os.path.join('cfg', src)
        if not os.path.exists(dstfile):
            copyfile(srcpath, dstfile)
        else:
            copyfile(srcpath, dstfile + '.new')

    bak_date = datetime.datetime.now().strftime(
        "%Y%m%d%H%M%S")

    for src in srcfiles_overwrite:
        dstfile = os.path.join(dstdir, src)
        srcpath = os.path.join('cfg', src)
        if not os.path.exists(dstfile):
            copyfile(srcpath, dstfile)
        else:
            move(dstfile, dstfile + '.bak.' + bak_date)
            copyfile(srcpath, dstfile)


class Install(_install):
    def run(self):
        _install.run(self)
        copy_config()


cmdclass = versioneer.get_cmdclass()
cmdclass['install'] = Install

setup(
    version=versioneer.get_version(),
    packages=['cloudmap', ],
    cmdclass=cmdclass,
)
