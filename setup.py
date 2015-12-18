from __future__ import print_function
# from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
from setuptools import setup

from setuptools.command.install import install as _install
import os
import versioneer
import sys

versioneer.VCS = 'git'
versioneer.versionfile_source = 'cloudmap/_version.py'
versioneer.versionfile_build = 'cloudmap/_version.py'
versioneer.tag_prefix = ''  # tags are like 1.2.0
versioneer.parentdir_prefix = 'CreateCloudMap-'


def mkdir_p(path):
    import errno
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def copy_config():
    try:
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


class Install(_install):
    def run(self):
        _install.run(self)
        copy_config()

cmdclass = versioneer.get_cmdclass()
cmdclass['install'] = Install

if sys.version_info >= (3, 2):
    install_requires = ['pyresample', 'numpy', 'scipy', 'requests', 'datetime',
                        'pillowfight', 'setuptools>=0.7.2',
                        'configparser==3.5.0b1']
else:
    install_requires = ['pyresample', 'numpy', 'scipy', 'requests', 'datetime',
                        'pillowfight', 'setuptools>=0.7.2', 'configparser']

setup(
    name='CreateCloudMap',
    version=versioneer.get_version(),
    packages=['cloudmap', ],
    cmdclass=cmdclass,
    license='GPL3',
    description='Create a cloud map for xplanet using satellite images ' +
                'from the Dundee Satellite Receiving Station',
    long_description=open('README.rst').read(),
    author='Joachim Herb',
    author_email='Joachim.Herb@gmx.de',
    url='https://github.com/jmozmoz/cloudmap',
    install_requires=install_requires,
    extras_require={
        'cartopy':  ["cartopy", "shapely", "pyshp"],
        'debug_pyresample': ["basemap", "matplotlib"],
        'debug_cartopy': ["matplotlib"]
    },
    entry_points={
        'console_scripts': [
            'create_map = cloudmap.create_map:main',
        ]
    },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
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
    scripts=['winpostinstall.py'],
    options={
        "bdist_wininst": {
            "install_script": "winpostinstall.py",
        },
    }
)
