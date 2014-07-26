from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from StringIO import StringIO
import numpy as np
import requests
import os
import datetime
import glob
from pyresample import image, geometry
from PIL import Image


class SatelliteData(object):

    # size of the output image
    outwidth = 0
    outheight = 0

    def __init__(self, longitude, extent, false_y, rescale, base_url, suffix):
        self.longitude = longitude
        self.extent = extent
        self.false_y = false_y
        self.rescale = rescale
        self.base_url = base_url
        self.suffix = suffix
        self.rescale = rescale
        self.filemodtime = 0

    def login(self, username, password):
        self.username = username
        self.password = password

#     @staticmethod
#     def curve(b):
#         """Rescale the brightness values used for MTSAT2 satellite"""
#         return np.minimum(b * 255.0 / 193.0, 255)
#
#     @staticmethod
#     def ID(b):
#         """Identity function"""
#         return b

    def set_time(self, dt, tempdir=""):
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
        str3 = "*_*_*_*"
        self.url = self.base_url + str1 + str2 + self.suffix
        self.filename = os.path.join(tempdir, str2 + self.suffix)
        self.purge_pattern = os.path.join(tempdir, str3 + self.suffix)

    def purge(self):
        for fl in glob.glob(self.purge_pattern):
            if fl == self.filename:
                continue
            os.remove(fl)

    def check_for_image(self):
        if os.path.isfile(self.filename):
            return True
        r = requests.head(self.url, auth=(self.username, self.password))
        if r.status_code == requests.codes.ok:
            return True
        else:
            return False

    def download_image(self):
        if os.path.isfile(self.filename):
            self.filemodtime = os.path.getmtime(self.filename)
            return
        r = requests.get(self.url, auth=(self.username, self.password))
        i = Image.open(StringIO(r.content))
        i.save(self.filename)
        self.filemodtime = os.path.getmtime(self.filename)

    def findStartIndex(self, img):
        """Return the first row index not containing the white
        border at the top"""

        look = False
        start = 3
        i = start
        left = 10
        right = img.shape[0] - 10
        for r in img[start:]:
            m = np.amin(r[left:right])
            if (look and m < 255):
                return i
            elif (not look and m == 255):
                look = True
            i = i + 1
        return 0

    def cut_borders(self):
        """Remove the white border of a satellite images (including text)"""

        x1 = self.findStartIndex(self.data)
        self.data = self.data[x1:, :]
        self.data = self.data[::-1]
        x2 = self.findStartIndex(self.data)
        self.data = self.data[x2:, :]
        self.data = self.data[::-1]

        self.data = self.data.T
        x1 = self.findStartIndex(self.data)
        self.data = self.data[x1:, :]
        self.data = self.data[::-1]
        x2 = self.findStartIndex(self.data)
        self.data = self.data[x2:, :]
        self.data = self.data[::-1]
        return self.data.T

    @staticmethod
    def pc():
        proj_dict = {'proj': 'eqc'}
        area_extent = (-20037508.34, -10018754.17, 20037508.34, 10018754.17)
        x_size = SatelliteData.outwidth
        y_size = SatelliteData.outheight
        pc = geometry.AreaDefinition('pc', 'Plate Carree world map', 'pc',
                                     proj_dict, x_size, y_size, area_extent)
        return pc

    def project(self, q=None):
        """Reproject the satellite image on an equirectangular map"""

        img = Image.open(self.filename).convert("L")
        self.data = np.array(img)
        self.data = self.cut_borders()

        x_size = self.data.shape[1]
        y_size = self.data.shape[0]
        proj_dict = {'a': '6378169.0', 'b': '6356584.0',
                     'lon_0': self.longitude,
                     'y_0': self.false_y,
                     'h': '35785831.0', 'proj': 'geos'}
        area_extent = (-self.extent, -self.extent,
                       self.extent, self.extent)
        area = geometry.AreaDefinition('geo', 'geostat', 'geo',
                                       proj_dict, x_size,
                                       y_size, area_extent)
        dataIC = image.ImageContainerQuick(self.data, area)

#         msg_con_nn = image.ImageContainerNearest(data, area,
#                                                  radius_of_influence=50000)

        SatelliteData.outwidth = self.outwidth
        SatelliteData.outheight = self.outheight

        dataResampled = dataIC.resample(SatelliteData.pc())
        dataResampledImage = self.rescale(dataResampled.image_data)

        # create fantasy polar clouds by mirroring high latitude data
        polar_height = int(90.0 / 1024.0 * SatelliteData.outheight)
        north_pole_indices = range(0, polar_height)
        north_pole_copy_indices = range(2 * polar_height, polar_height, -1)
        dataResampledImage[north_pole_indices, :] =\
            dataResampledImage[north_pole_copy_indices, :]
        south_pole_indices = range(SatelliteData.outheight - polar_height,
                                   SatelliteData.outheight)
        south_pole_copy_indices = range(SatelliteData.outheight - polar_height,
                                        SatelliteData.outheight -
                                        2 * polar_height,
                                        -1)
        dataResampledImage[south_pole_indices, :] = \
            dataResampledImage[south_pole_copy_indices, :]

        width = 55
        weight = np.array([max((width - \
                                min([abs(self.longitude - x),
                                abs(self.longitude - x + 360),
                                abs(self.longitude - x - 360)])) / 180,
                               1e-7) \
                           for x in np.linspace(-180,
                                                180,
                                                dataResampled.shape[1])])
        result = np.array([dataResampledImage,
                          np.tile(weight, (dataResampled.shape[0], 1))])
        if q:
            q.put(result)
        else:
            return result
