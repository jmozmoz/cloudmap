CreateCloudMap
==============

.. image:: https://img.shields.io/pypi/v/CreateCloudMap.svg
    :target: https://pypi.python.org/pypi/createcloudmap

.. image:: https://img.shields.io/pypi/pyversions/CreateCloudMap.svg
    :target: https://pypi.python.org/pypi/createcloudmap

.. image:: https://img.shields.io/pypi/l/CreateCloudMap.svg
    :target: https://pypi.python.org/pypi/createcloudmap

Python script to create a cloud map for xplanet using satellite images from the
`Dundee Satellite Receiving Station, Dundee University, UK <http://www.sat.dundee.ac.uk/>`_.
This script can also be installed by pip from `pypi <https://pypi.python.org/pypi/CreateCloudMap>`_.

`xplanet <http://xplanet.sourceforge.net/>`_ can use a cloud map to make the earth look more pretty.


There is a free service which create one such cloud map per day. Due to a temporary unavailability
of that service this script `create_map` was developed to automatically download the necessary geostationary images
from the `Dundee Satellite Receiving Station, Dundee University, UK <http://www.sat.dundee.ac.uk/>`_.
To use this service you need an account there (which is free). Also a new cloud map can be created every three hours.

Set your login information in the configuration file (default name for UNIX-like systems: ``$HOME/.CreateCloudMap/CreateCloudMap.ini``, for Windows: ``%HOME%\.CreateCloudMap\CreateCloudMap.ini``)::

  [Download]
  username = user
  password = secret
  tempdir = images
  # Use one of the following for resolution: low, medium, high
  resolution = medium
  purge = false

  [xplanet]
  destinationdir = xplanet/images
  destinationfile = clouds_2048.jpg
  width = 2048
  height = 1024

  [processing]
  nprocs = 1
  # use either pyresample or cartopy
  projection = pyresample

If the configuration file already exists, a new version is copied to ``CreateCloudMap.ini.new`` to not overwrite the login data.
The old config file should work after an update, because default values are used for
newly introduced options.

``tempdir`` specifies the directory where the downloaded images (and if enabled by the command line
switch ``--debug`` or ``-d``) intermediate debug images are stored. ``destinationdir`` specifies the directory where
the output ``destinationfile`` is saved.

``resolution`` can be set to ``low``, ``medium`` or ``high`` to determine the resolution
of the downloaded satellite images.

If ``purge`` is set to true old satellite images will be deleted which are not
used to draw the current cloud map.

``width`` and ``height`` set the dimensions of the cloud map in ``destinationfile``.

``nprocs`` specifies the number of processors to be used for the processing of the
satellite images. If this number is larger than 1 the multiprocessing library
will be used to create separate processes communicating sending back their
results by queues.

``projection`` specifies the Python library used for projecting the geostationary
images onto a flat map. Possible values are ``pyresample`` and ``cartopy``.
``pyresample`` is the standard value and this library is set as dependency, so
it is installed during the installation of ``CreateCloudMap`` (if pip is used to
install it). If ``cartopy`` is used, this library must be installed manually.
``cartopy`` is (currently much) slower than ``pyresample``.


To see all command line options of the script use ``--help``::

  $ create_map --help
  usage: create_map [-h] [-d] [-c FILE] [-f]

  optional arguments:
    -h, --help            show this help message and exit
    -d, --debug           store intermediate results
    -c FILE, --conf_file FILE
                          Specify config file
    -f, --force           Force to recreate cloud map

Dependencies
............
To automatically install ``cartopy`` use the following command line for pip::

  pip install CreateCloudMap[cartopy]


For the debug output to work with the ``pyresample`` projection the
libraries matplotlib and basemap have to be installed. This can be done either
manually or by giving the extra requirement option ``[debug_pyresample]``
when using pip::

  pip install CreateCloudMap[debug_pyresample]

For the debug output to work with the ``cartopy`` projection the
library matplotlib is necessary. It can be automatically installed by using
pip::

  pip install CreateCloudMap[cartopy,debug_cartopy]


(So if no extra dependency is given the pyresample library will be installed
(if it has not been already installed) and no debug output is possible)

References
..........
A nice description of the concepts forming the basis of this program can be found
at `this blog post <https://apollo.open-resource.org/mission:log:2014:06:17:new-fresh-global-cloudmap-distribution-service-xplanet>`_.
