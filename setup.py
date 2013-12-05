from setuptools import setup
import os
 
setup(
    name='CreateCloudMap',
    version='0.1.0',
    packages=['cloudmap', ],
    license='LICENSE',
    description='Create a cloud map for xplanet using satellite images from the Dundee Satellite Receiving Station, Dundee University, UK',
    long_description=open('README.md').read(),
    author='Joachim Herb',
    author_email='Joachim.Herb@gmx.de',
    install_requires=['pyresample', 'numpy', 'scipy', 'requests', 'datetime', 
                      'argparse', 'ConfigParser', 'PIL'],
    entry_points={
        'console_scripts': [
            'create_map = cloudmap.create_map:main',
        ]
    }
)

def mkdir_p(path):
    import errno
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

from sys import argv
try:
    if argv[1] == 'install':
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
            
except IndexError: pass