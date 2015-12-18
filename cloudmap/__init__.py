from .geo_dundee import GeoSatelliteDataDundee
from .geo_jma import GeoSatelliteDataJMA
from .polar import PolarSatelliteData
from .satellites import Satellites
from .mkdir import mkdir_p

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions