from __future__ import print_function
# from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
from setuptools import setup

from setuptools.command.install import install as _install
import os
import versioneer
import sys
import datetime
from pathlib import Path

versioneer.VCS = 'git'
versioneer.versionfile_source = 'cloudmap/_version.py'
versioneer.versionfile_build = 'cloudmap/_version.py'
versioneer.tag_prefix = ''  # tags are like 1.2.0
versioneer.parentdir_prefix = 'CreateCloudMap-'


def copy_config():
    from shutil import copyfile, move
    srcfiles = [
        'CreateCloudMap.ini',
    ]
    srcfiles_overwrite = [
        'satellites.json'
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

install_requires = ['requests', 'setuptools>=0.7.2']

setup(
    name='CreateCloudMap',
    version=versioneer.get_version(),
    packages=['cloudmap', ],
    cmdclass=cmdclass,
    license='GPL3',
    description='Downloads a cloud map for xplanet from ' +
                'https://clouds.matteason.co.uk/',
    long_description=open('README.rst').read(),
    author='Joachim Herb',
    author_email='Joachim.Herb@gmx.de',
    url='https://github.com/jmozmoz/cloudmap',
    install_requires=install_requires,
    extras_require={
    },
    entry_points={
        'console_scripts': [
            'create_map = cloudmap.create_map:main',
        ]
    },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Desktop Environment",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Utilities",
    ],
    zip_safe=False,
)
