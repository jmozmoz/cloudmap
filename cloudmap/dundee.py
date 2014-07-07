from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from mkdir import mkdir_p
from satellite import SatelliteData

import sys
import datetime
import numpy as np
import os
from PIL import Image


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


def saveImage(new_image, filename):
    """Save satellite image"""

    img = Image.fromarray(new_image).convert('RGB')
    img.save(filename)


class Dundee(object):
    def __init__(self, resolution, username, password, tempdir):
        self.username = username
        self.password = password
        self.tempdir = tempdir

        resolution_str = {'medium': 'S2',
                          'high': 'S1'}

        try:
            resfile = resolution_str[resolution]
        except KeyError:
            sys.exit('Wrong resolution specified in config file! ' +
                     resolution +
                     ' Valid values are: medium, high')

        self.satellite_list = (
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

    def find_latest(self):
        dt = datetime.datetime.utcnow()
        max_tries = 10

        for _ in range(max_tries):
            found_all = True

            for satellite in self.satellite_list:
                satellite.login(self.username, self.password)
                satellite.set_time(dt, self.tempdir)
                found_all = found_all and satellite.check_for_image()

            if found_all:
                break
            dt = dt - datetime.timedelta(hours=3)

        if not found_all:
            sys.exit("Cannot download (all) satellite images!")

        return self.satellite_list[0].dt

    def download(self, purge):
        latest_download = 0
        for satellite in self.satellite_list:
            if purge:
                satellite.purge()
            print("Satellite file: " + satellite.filename)
            satellite.download_image()
            latest_download = max(latest_download, satellite.filemodtime)

        return latest_download

    def overlay(self, debug):
        mkdir_p(self.tempdir)

        self.out_image = np.empty(shape=(SatelliteData.outheight,
                     SatelliteData.outwidth))

        weight_sum = np.empty(shape=(SatelliteData.outheight,
                                 SatelliteData.outwidth))

        i = 1
        for satellite in self.satellite_list:
            img = satellite.project()
            if debug:
                saveDebug(img[0],
                          os.path.join(self.tempdir, "test" + repr(i) +
                                       ".jpeg"))
                saveDebug(img[1],
                          os.path.join(self.tempdir, "weighttest" + repr(i) +
                                       ".jpeg"))
            i += 1
            weight_sum = weight_sum + img[1]
            self.out_image = self.out_image + (img[0] * img[1])

        if debug:
            saveDebug(weight_sum,
                      os.path.join(self.tempdir, "weightsum.jpeg"))

        self.out_image = self.out_image / weight_sum
        if debug:
            saveDebug(self.out_image,
                      os.path.join(self.tempdir, "test.jpeg"))

    def save_image(self, outdir, outfile):
        mkdir_p(outdir)

        try:
            os.remove(os.path.join(outdir, outfile))
        except OSError:
            pass
        saveImage(self.out_image, os.path.join(outdir, outfile))
