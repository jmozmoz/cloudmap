from .satellite import SatelliteData
from .dundee import Dundee
from .mkdir import mkdir_p

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions