from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from .mkdir import mkdir_p
from .geo_dundee import GeoSatelliteDataDundee
#  from .polar import PolarSatelliteData
from .geo_jma import GeoSatelliteDataJMA

import sys
import datetime
import numpy as np
import os
from PIL import Image
import json

def curve(b):
    """Rescale the brightness values used for MTSAT2 satellite"""

    return np.minimum(b * 255.0 / 193.0, 255)


def curve2(b):
    """Rescale the brightness values used for MTSAT2 satellite"""

    return np.minimum(b * 255.0 / 150.0, 255)


def ID(b):
    """Identity function"""

    return b


def saveDebug(weight_sum, filename):
    """
    Save image for debugging onto map with grid and coastlines
    """
    if Satellites.projection_method == "pyresample":
        saveDebug_pyresample(weight_sum, filename)
    else:
        saveDebug_cartopy(weight_sum, filename)


def saveDebug_cartopy(weight_sum, filename):
    """
    Save image for debugging onto map with grid and coastlines using
    cartopy
    """
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import matplotlib.cm as cm

    width = Satellites.outwidth
    height = Satellites.outheight

    fig = plt.figure(frameon=False, dpi=1, figsize=(width, height))
    ax = plt.axes([0., 0., 1., 1.], projection=ccrs.PlateCarree())
    fig.add_axes(ax)
    ax.set_global()
    ax.set_axis_off()

    weight_sum = weight_sum / np.max(weight_sum) * 255.0

    ax.imshow(weight_sum, origin='upper',
              vmin=0, vmax=255,
              extent=(-180, 180, -90, 90),
              cmap=cm.Greys_r,  # @UndefinedVariable
              )

    ax.gridlines(draw_labels=False, axes=0, linewidth=10)
#    ax.add_feature(cfeature.OCEAN, facecolor='aqua', alpha='0.1')
    ax.add_feature(cfeature.BORDERS, alpha='0.2', linewidth="20")
    ax.coastlines(resolution='50m', color='black', linewidth="20")

    fig.canvas.draw()
    plt.savefig(filename, bbox_inches='tight', pad_inches=0, dpi=1)


def saveDebug_pyresample(weight_sum, filename):
    """
    Save image for debugging onto map with grid and coastlines using
    pyresample
    """

    import matplotlib
    matplotlib.use('AGG', warn=False)
    from pyresample import plot
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm

    new_image = np.array(255.0 * weight_sum / np.max(weight_sum),
                         'uint8')
    bmap = plot.area_def2basemap(pc(Satellites.outwidth,
                                    Satellites.outheight),
                                 resolution='c')
    bmap.drawcoastlines(linewidth=0.2, color='red')
    bmap.drawmeridians(np.arange(-180, 180, 10), linewidth=0.2, color='red')
    bmap.drawparallels(np.arange(-90, 90, 10), linewidth=0.2, color='red')
    bmap.imshow(new_image, origin='upper', vmin=0, vmax=255,
                cmap=cm.Greys_r)  # @UndefinedVariable
#    plt.show()

    i = datetime.datetime.utcnow()
    plt.text(0, -75, "%s UTC" % i.isoformat(),
             color='green', size=15,
             horizontalalignment='center')
    plt.savefig(filename, bbox_inches='tight', pad_inches=0, dpi=400)
    plt.close()


def saveImage(new_image, filename):
    """Save satellite image"""

    img = Image.fromarray(new_image).convert('RGB')
    img.save(filename)


def do_project(satellite):
    """Wrap the project method to use multiprocessing pool"""
    return satellite.project()


def pc(x_size, y_size):
    from pyresample import geometry
    """Create area defintion for world map in Plate Carree projection"""
    proj_dict = {'proj': 'eqc'}
    area_extent = (-20037508.34, -10018754.17, 20037508.34, 10018754.17)
    pc = geometry.AreaDefinition('pc', 'Plate Carree world map', 'pc',
                                 proj_dict, x_size, y_size, area_extent)
    return pc


class Satellites(object):

    """
    Class to download and process all images from the Satellites server
    """

    # size of the output image
    outwidth = 0
    outheight = 0
    projection_method = "pyresample"

    def __init__(self, resolution, username, password, tempdir, nprocs=1,
                 debug=False):
        """
        Args:
            * resolution:
                resolution of the image to be downloaded (low, medium, high)
            * username:
                username of Satellites account
            * password:
                password of Satellites account
            * tempdir:
                directory to store downloaded images (will be created
                if necessary)
            * nprocs:
                number of processors to used for image processing
        """

        self.username = username
        self.password = password
        self.tempdir = tempdir
        self.nprocs = nprocs

        jsonfile = os.path.expanduser("~/.CreateCloudMap/satellites.json")
        satellite_json = json.load(open(jsonfile))
        self.satellite_list = []

        for s in satellite_json:
            rescale = ID if s['rescale'] == "ID" else None

            if 'resolution_str' in s:
                resolution_str = s['resolution_str']
            else:
                resolution_str = {'low': 'S4',
                                  'medium': 'S2',
                                  'high': 'S1'}

            if 'resolution_mult' in s:
                resolution_mult = s['resolution_mult']
            else:
                resolution_mult = {'low': 1,
                                   'medium': 2,
                                   'high': 4}

            if s['type'] == 'geoDundee':
                self.satellite_list.append(GeoSatelliteDataDundee(
                    longitude=s['longitude'],
                    limit=s['limit'],
                    base_url=s['base_url'],
                    suffix=s['suffix'],
                    resolution=resolution,
                    resolution_str=resolution_str,
                    resolution_mult=resolution_mult,
                    debug=debug,
                    rescale=rescale
                ))
            elif s['type'] == 'geoJMA':
                self.satellite_list.append(GeoSatelliteDataJMA(
                    longitude=s['longitude'],
                    limit=s['limit'],
                    base_url=s['base_url'],
                    suffix=s['suffix'],
                    resolution=resolution,
                    debug=debug,
                    rescale=rescale
                ))

    def find_latest(self):
        """
        Find the latest time for which all satellite images can
        be downloaded
        """
        dt = datetime.datetime.utcnow()
        max_tries = 200

        print("Search backward for images from:", dt)

        for _ in range(max_tries):
            found_all = True

            for satellite in self.satellite_list:
                satellite.login(self.username, self.password)
                satellite.set_time(dt, self.tempdir)
                found_all = found_all and satellite.check_for_image()

            if found_all:
                break
            dt = dt - datetime.timedelta(hours=1)

        if not found_all:
            sys.exit("Cannot download (all) satellite images!")

        return self.satellite_list[0].dt

    def download(self, purge):
        """
        Download all satellite images

        Args:
            * purge:
                Should all old satellite images be purged
        """

        mkdir_p(self.tempdir)

        latest_download = 0
        for satellite in self.satellite_list:
            if purge:
                satellite.purge()
            print("Satellite file: " + satellite.filename)
            satellite.download_image()
            latest_download = max(latest_download, satellite.filemodtime)

        return latest_download

    def overlay(self, debug):
        """
        Create overlay of all satellite images onto one world map

        Args:
            * debug:
                Should images created during the image processing be saved
        """

        self.out_image = np.zeros(shape=(Satellites.outheight,
                                         Satellites.outwidth))

        weight_sum = np.zeros(shape=(Satellites.outheight,
                                     Satellites.outwidth))

        if self.nprocs == 1:
            i = 1
            for satellite in self.satellite_list:
                # put class variables into object variables to get it to
                # work with multiprocessing
                satellite.outwidth = Satellites.outwidth
                satellite.outheight = Satellites.outheight
                satellite.projection_method = \
                    Satellites.projection_method
                img = satellite.project()
                if debug:
                    self.imageDebug(i, img)
                i += 1
                weight_sum = weight_sum + img[1]
                self.out_image = self.out_image + (img[0] * img[1])
        else:
            from multiprocessing import Pool
            pool = Pool(processes=self.nprocs)

            for satellite in self.satellite_list:
                satellite.outwidth = Satellites.outwidth
                satellite.outheight = Satellites.outheight
                satellite.projection_method = \
                    Satellites.projection_method

            images = pool.map(do_project, self.satellite_list)
            i = 1
            for img in images:
                if debug:
                    self.imageDebug(i, img)
                weight_sum = weight_sum + img[1]
                self.out_image = self.out_image + (img[0] * img[1])
                i += 1

        self.out_image = self.out_image / weight_sum

        if debug:
            saveDebug(weight_sum,
                      os.path.join(self.tempdir, "weightsum.jpeg"))
            saveDebug(self.out_image,
                      os.path.join(self.tempdir, "test.jpeg"))

    def save_image(self, outdir, outfile):
        """
        Save the created world satellite image

        Args:
            * outdir:
                Directory the image should be saved in
            * outfile:
                Filename of the image
        """

        mkdir_p(outdir)

        try:
            os.remove(os.path.join(outdir, outfile))
        except OSError:
            pass
        saveImage(self.out_image, os.path.join(outdir, outfile))

    def imageDebug(self, i, img):
        """
        Save intermediary image and corresponding local weighting values

        Args:
            * i:
                sequential number of image
            * img:
                two dimensional array containing two images
                (the real image and the weighting values)
        """

        saveDebug(img[0],
                  os.path.join(self.tempdir, "test" +
                               repr(i) + ".jpeg"))
        saveDebug(img[1],
                  os.path.join(self.tempdir, "weighttest" +
                               repr(i) + ".jpeg"))
