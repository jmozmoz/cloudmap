CreateCloudMap
==============

.. image:: https://img.shields.io/pypi/v/CreateCloudMap.svg
    :target: https://pypi.python.org/pypi/createcloudmap

.. image:: https://img.shields.io/pypi/pyversions/CreateCloudMap.svg
    :target: https://pypi.python.org/pypi/createcloudmap

.. image:: https://img.shields.io/pypi/l/CreateCloudMap.svg
    :target: https://pypi.python.org/pypi/createcloudmap

.. image:: https://github.com/jmozmoz/cloudmap/actions/workflows/python-package.yml/badge.svg

Python script to create a cloud map for xplanet using the cloud map provided
by https://clouds.matteason.co.uk/.
This script can also be installed by pip from `pypi <https://pypi.python.org/pypi/CreateCloudMap>`_.

`xplanet <https://xplanet.sourceforge.net/>`_ can use a cloud map to make the earth look more pretty.

The script automatically checks, if a new image is available. The default
behavior is to only download the image, if it is new.

Set the desired image size in the configuration file together with the output path
(default name for UNIX-like systems: ``$HOME/.CreateCloudMap/CreateCloudMap.ini``,
for Windows: ``%HOME%\.CreateCloudMap\CreateCloudMap.ini``)::

  [xplanet]
  destinationdir = xplanet/images
  destinationfile = clouds_2048.jpg
  width = 2048
  height = 1024

If the configuration file already exists, a new version is copied to ``CreateCloudMap.ini.new``
to not overwrite the existing settings.
The old config file should work after an update, because default values are used for
newly introduced options.

``width`` and ``height`` set the dimensions of the cloud map in ``destinationfile``.
Only resolutions available at https://clouds.matteason.co.uk/ are supported.

To see all command line options of the script use ``--help``::

  $ create_map --help
  usage: create_map.py [-h] [-d] [-c FILE] [-f] [-V]

  options:
    -h, --help            show this help message and exit
    -d, --debug           debug outputs
    -c FILE, --conf_file FILE
                          Specify config file
    -f, --force           Force to recreate cloud map
    -V, --version         show program's version number and exit

