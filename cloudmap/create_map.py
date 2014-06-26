#!/usr/bin/env python
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from PIL import Image
from pyresample import image, geometry

from StringIO import StringIO
import numpy as np
import requests
import os
import datetime
import argparse
import ConfigParser
import sys
import errno
import glob


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def saveImage(new_image, filename):
    """Save satellite image"""

    img = Image.fromarray(new_image).convert('RGB')
    img.save(filename)


def saveDebug(weight_sum, filename):
    import matplotlib
    matplotlib.use('AGG', warn=False)
    from pyresample import plot
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm

    new_image = np.array(255.0 * weight_sum / np.max(weight_sum[:, :]),
                         'uint8')
    bmap = plot.area_def2basemap(SatelliteData.pc(), resolution='c')
    bmap.drawcoastlines()
    bmap.drawmeridians(np.arange(-180, 180, 45))
    bmap.drawparallels(np.arange(-90, 90, 10))
    bmap.imshow(new_image, origin='upper', vmin=0, vmax=255,
                cmap=cm.Greys_r)
    plt.savefig(filename, bbox_inches='tight', pad_inches=0, dpi=200)
    plt.close()


class SatelliteData:

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

    @staticmethod
    def curve(b):
        """Rescale the brightness values used for MTSAT2 satellite"""
        return np.minimum(b * 255.0 / 193.0, 255)

    @staticmethod
    def ID(b):
        """Identity function"""
        return b

    def set_time(self, dt, tempdir=""):
        self.dt = datetime.datetime(dt.year, dt.month, dt.day,
                                    int(int(dt.hour / 3) * 3), 0, 0)
        day = self.dt.strftime("%d").lstrip("0")
        month = self.dt.strftime("%m").lstrip("0")
        hour = self.dt.strftime("%H").lstrip("0")
        str1 = self.dt.strftime("%Y/") + month + "/" + day + "/" + hour + "00/"
        str2 = self.dt.strftime("%Y_") + month + "_" + day + "_" + hour + "00"
        str3 = "*_*_*_*00"
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

    def project(self):
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
        return np.array([dataResampledImage,
                         np.tile(weight, (dataResampled.shape[0], 1))])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="store intermediate results",
                        action="store_true")
    parser.add_argument("-c", "--conf_file", help="Specify config file",
                        metavar="FILE",
                        default=os.path.expanduser(
                           "~/.CreateCloudMap/CreateCloudMap.ini"))
    parser.add_argument("-f", "--force", help="Force to recreate cloud map",
                        action="store_true")
    args = parser.parse_args()
    config = ConfigParser.SafeConfigParser(
                                       {'width': '2048',
                                        'height': '1024',
                                        'destinationfile': 'clouds_2048.jpg',
                                        'resolution': 'medium',
                                        'purge': 'false'}
                                       )
    config.read([args.conf_file])

    username = config.get("Download", 'username')
    password = config.get("Download", 'password')
    tempdir = config.get("Download", 'tempdir')
    resolution = config.get("Download", 'resolution')
    purge = config.get("Download", 'purge').lower() == 'true'

    outdir = config.get("xplanet", 'destinationdir')
    outfile = config.get("xplanet", 'destinationfile')
    SatelliteData.outwidth = int(config.get("xplanet", 'width'))
    SatelliteData.outheight = int(config.get("xplanet", 'height'))

    resolution_str = {'medium': 'S2',
                      'high': 'S1'}

    try:
        resfile = resolution_str[resolution]
    except KeyError:
        sys.exit('Wrong resolution specified in config file! ' +
                 resolution +
                 ' Valid values are: medium, high')

    satellite_list = (
          SatelliteData(145.0, 5433878.562 * 1.01, 50000,
                        SatelliteData.curve,
                        "http://www.sat.dundee.ac.uk/xrit/145.0E/MTSAT/",
                        "_MTSAT2_4_" + resfile + ".jpeg"
                        ),
          SatelliteData(57.0, 5568742.4 * 0.97, 0,
                        SatelliteData.ID,
                        "http://www.sat.dundee.ac.uk/xrit/057.0E/MET/",
                        "_MET7_2_" + resfile + ".jpeg"
                        ),
          SatelliteData(0.0, 5433878.562, 0,
                        SatelliteData.ID,
                        "http://www.sat.dundee.ac.uk/xrit/000.0E/MSG/",
                        "_MSG3_9_" + resfile + ".jpeg"
                        ),
          SatelliteData(-75.0, 5433878.562, 0,
                        SatelliteData.ID,
                        "http://www.sat.dundee.ac.uk/xrit/075.0W/GOES/",
                        "_GOES13_4_" + resfile + ".jpeg"
                        ),
          SatelliteData(-135.0, 5433878.562, 0,
                        SatelliteData.ID,
                        "http://www.sat.dundee.ac.uk/xrit/135.0W/GOES/",
                        "_GOES15_4_" + resfile + ".jpeg"
                        ),
          )

    dt = datetime.datetime.utcnow()
    max_tries = 10

    for _ in range(max_tries):
        found_all = True

        for satellite in satellite_list:
            satellite.login(username, password)
            satellite.set_time(dt, tempdir)
            found_all = found_all and satellite.check_for_image()

        if found_all:
            break
        dt = dt - datetime.timedelta(hours=3)

    if not found_all:
        sys.exit("Cannot download (all) satellite images!")

    print("Download image date/time: ",
          satellite_list[0].dt.strftime("%Y-%m-%d %H:00 UTC"))

    mkdir_p(tempdir)

    latest_download = 0
    for satellite in satellite_list:
        if purge:
            satellite.purge()
        print("Satellite file: " + satellite.filename)
        satellite.download_image()
        latest_download = max(latest_download, satellite.filemodtime)

    if (
        not args.force and
        os.path.isfile(os.path.join(outdir, outfile)) and
        (os.path.getmtime(os.path.join(outdir, outfile))
         > latest_download)
        ):
        sys.exit(0)

    new_image = np.empty(shape=(SatelliteData.outheight,
                             SatelliteData.outwidth))

    weight_sum = np.empty(shape=(SatelliteData.outheight,
                             SatelliteData.outwidth))

    i = 1
    for satellite in satellite_list:
        img = satellite.project()
        if args.debug:
            saveDebug(img[0],
                      os.path.join(tempdir, "test" + repr(i) + ".jpeg"))
            saveDebug(img[1],
                      os.path.join(tempdir, "weighttest" + repr(i) + ".jpeg"))
        i += 1
        weight_sum = weight_sum + img[1]
        new_image = new_image + (img[0] * img[1])

    if args.debug:
        saveDebug(weight_sum,
                  os.path.join(tempdir, "weightsum.jpeg"))

    new_image = new_image / weight_sum
    mkdir_p(outdir)

    try:
        os.remove(os.path.join(outdir, outfile))
    except OSError:
        pass
    saveImage(new_image, os.path.join(outdir, outfile))
    if args.debug:
        saveDebug(new_image,
                  os.path.join(tempdir, "test.jpeg"))
    print("finished")

if __name__ == '__main__':
    main()
