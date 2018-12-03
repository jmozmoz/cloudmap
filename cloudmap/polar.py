from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from io import BytesIO
import numpy as np
import requests
import os
import datetime
import glob
from PIL import Image
from numpy.core.umath import sign


class PolarSatelliteData(object):

    """
    A class to download and process satellite image
    """

    def __init__(self, longitude, latitude, extent,
                 base_url, rescale, weight_width, suffix, debug):
        """
        Args:

            * longitude:
                the longitude the satellite is positioned
            * latitude:
                the latitude, i.e. the pole used for the stereographic
                projection
            * extent:
                the limits of the area covered by the satellite image
            * base_url:
                the url the image to download
        """

        self.longitude = longitude
        self.latitude = latitude
        self.extent = extent
        self.base_url = "https://www.aviationweather.gov/data/obs/sat/intl/"
        self.suffix = suffix + ".jpg"
        self.rescale = rescale
        self.filemodtime = 0
        self.outwidth = 0
        self.outheight = 0
        self.weight_width = weight_width
        self.projection_method = "pyresample"
        self.debug = debug

    def login(self, username, password):
        pass

    def set_time(self, dt, tempdir=""):
        """
        Setup satellite download image name based on time

        Args:
            * dt:
                datetime representation of time satellite image was taken
            * tempdir:
                directory to store downloaded images
        """
        self.dt = datetime.datetime(dt.year, dt.month, dt.day,
                                    int((dt.hour // 3) * 3), 0, 0)
        day = self.dt.strftime("%d").lstrip("0")
        month = self.dt.strftime("%m").lstrip("0")
        hour = self.dt.strftime("%H").lstrip("0")
        if not hour:  # if hour empty then assume midnight
            str1 = self.dt.strftime("%Y/") + month + "/" + day + "/" + "0/"
            str2 = self.dt.strftime("%Y_") + month + "_" + day + "_" + "0"
        else:
            str1 = self.dt.strftime("%Y/") + month + "/" + day + \
                "/" + hour + "00/"
            str2 = self.dt.strftime("%Y_") + month + "_" + day + \
                "_" + hour + "00"
        str2 = '20151204_1815'
        str3 = "*_*"
        self.url = self.base_url + str2 + self.suffix
        self.filename = os.path.join(tempdir, str2 + self.suffix)
        self.purge_pattern = os.path.join(tempdir, str3 + self.suffix)

    def purge(self):
        """Remove old satellite images"""
        for fl in glob.glob(self.purge_pattern):
            if fl == self.filename:
                continue
            os.remove(fl)

    def check_for_image(self):
        """
        Test if image has already be downloaded or that it can be
        downloaded from the Dundee server
        """
        if os.path.isfile(self.filename):
            self.logger.debug("found image: %s" % self.filename)
            return True
        r = requests.head(self.url)
        if r.status_code == requests.codes.ok:  # @UndefinedVariable
            self.logger.debug("can download image: %s" % self.url)
            return True
        else:
            self.logger.debug("cannot download image: %s" % self.url)
            return False

    def download_image(self):
        """Download the image if it has not been downloaded before"""
        if os.path.isfile(self.filename):
            self.logger.debug("image has already been downloaded: %s" %
                              self.filename)
            self.filemodtime = os.path.getmtime(self.filename)
            return
        self.logger.info("download image: %s" % self.url)
        r = requests.get(self.url)
        i = Image.open(BytesIO(r.content))
        i.save(self.filename)
        self.filemodtime = os.path.getmtime(self.filename)

    def cut_borders(self, pil_im):
        """Remove the white border of a satellite images (including text)"""
        w, h = pil_im.size
        pil_im = pil_im.crop((0, 12, w, h))

        return pil_im

    def project(self):
        if self.projection_method == "pyresample":
            return self.project_pyresample()
        else:
            return self.project_cartopy()

    def project_cartopy(self):
        """
        Reproject the satellite image on an equirectangular map using the
        cartopy library
        """
        import cartopy.crs as ccrs
        from cartopy.img_transform import warp_array

        img = Image.open(self.filename).convert("L")
        self.data = self.cut_borders(img)

        width = self.outwidth
        height = self.outheight

        buf, _extent = \
            warp_array(self.data,
                       source_proj=ccrs.Geostationary(
                           central_longitude=self.longitude,
                           satellite_height=35785831.0
                       ),
                       target_proj=ccrs.PlateCarree(),
                       target_res=(width, height))

        dataResampledImage = self.rescale(buf.data)
#         dataResampledImage = self.polar_clouds(dataResampledImage)
        weight = self.get_weight()

        result = np.array([dataResampledImage, weight])
        return result

    def get_weight(self):
        """Get weighting function for satellite image for overlaying"""

        weight = np.array([max((self.weight_width -
                                min([abs(self.longitude - x),
                                    abs(self.longitude - x + 360),
                                    abs(self.longitude - x - 360)])) / 180,
                               1e-7)
                           for x in np.linspace(-180,
                                                180,
                                                self.outwidth)])

        weight = np.array([1/(2.5/9) * weight *
                           max(1e-7,
                               -sign(self.latitude) *
                               (i - self.outheight/2)/self.outheight*2 -
                               6.5/9)
                           for i in range(self.outheight)])

        return weight

    def project_pyresample(self):
        """
        Reproject the satellite image on an equirectangular map using the
        pyresample library
        """

        from pyresample import image, geometry
        from .satellites import pc
        from PIL import ImageFilter

        img = Image.open(self.filename).convert("L")
        img = self.cut_borders(img)

        # round away grid
        im2 = img.filter(ImageFilter.MedianFilter(3))
        # create mask for borders
        mask = img.point(lambda x: 0 if x < 250 else 255).filter(
            ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3))

        # create replacement picture with borders smoothed way
        # picture_count += 1
        im3 = im2.filter(ImageFilter.MinFilter(7))

        im4 = Image.composite(im3, im2, mask)
        self.data = np.array(im4)

        self.x_size = self.data.shape[1]
        self.y_size = self.data.shape[0]
        proj_dict = {'lon_0': self.longitude,
                     'lat_0': self.latitude,
                     'proj': 'stere',
                     'ellps': 'WGS84',
                     'units': 'm'}
        area = geometry.AreaDefinition('stere', 'stere', 'stere',
                                       proj_dict,
                                       self.x_size,
                                       self.y_size,
                                       self.extent)

        dataIC = image.ImageContainerQuick(self.data, area)
        dataResampled = dataIC.resample(pc(self.outwidth,
                                           self.outheight))
        dataResampledImage = self.rescale(dataResampled.image_data)
#        dataResampledImage = np.ones(shape=dataResampledImage.shape) * 1e-7

        weightResampledImage = self.get_weight()
#         weightIC = image.ImageContainerQuick(weight, area)
#         weightResampled = weightIC.resample(pc(self.outwidth,
#                                             self.outheight))
#         weightResampledImage = weightResampled.image_data
#         dataResampledImage = self.polar_clouds(dataResampledImage)

        self.logger.info("image max: %r" % np.max(dataResampledImage))

        result = np.array([dataResampledImage, weightResampledImage])
        return result
