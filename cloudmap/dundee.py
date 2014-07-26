from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from cloudmap import mkdir, SatelliteData

import sys
import datetime
import numpy as np
import os
from PIL import Image
import time


def curve(b):
    """Rescale the brightness values used for MTSAT2 satellite"""
    return np.minimum(b * 255.0 / 193.0, 255)


def ID(b):
    """Identity function"""
    return b


def saveDebug(weight_sum, filename):
    import matplotlib
    matplotlib.use('AGG', warn=False)
    from pyresample import plot
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm

    new_image = np.array(255.0 * weight_sum / np.max(weight_sum),
                         'uint8')
    bmap = plot.area_def2basemap(SatelliteData.pc(), resolution='c')
    bmap.drawcoastlines(linewidth=0.2, color='red')
    bmap.drawmeridians(np.arange(-180, 180, 45), linewidth=0.2, color='red')
    bmap.drawparallels(np.arange(-90, 90, 10), linewidth=0.2, color='red')
    bmap.imshow(new_image, origin='upper', vmin=0, vmax=255,
                cmap=cm.Greys_r)  # @UndefinedVariable
    plt.savefig(filename, bbox_inches='tight', pad_inches=0, dpi=400)
    plt.close()


def saveImage(new_image, filename):
    """Save satellite image"""

    img = Image.fromarray(new_image).convert('RGB')
    img.save(filename)


class Dundee(object):
    def __init__(self, resolution, username, password, tempdir, nprocs=1):
        self.username = username
        self.password = password
        self.tempdir = tempdir
        self.nprocs = nprocs

        self.satellite_list = (
              SatelliteData(longitude=145.0,
                            limit={'left': 9, 'right': 680,
                                   'top': 12, 'bottom': 683},
                            rescale=curve,
                            base_url="145.0E/MTSAT/",
                            suffix="_MTSAT2_4_",
                            resolution=resolution
                            ),
              SatelliteData(longitude=57.0,
                            limit={'left': 13, 'right': 612,
                                   'top': 13, 'bottom': 612},
                            rescale=ID,
                            base_url="057.0E/MET/",
                            suffix="_MET7_2_",
                            resolution=resolution
                            ),
              SatelliteData(longitude=0.0,
                            limit={'left': 16, 'right': 913,
                                   'top': 16, 'bottom': 913},
                            rescale=ID,
                            base_url="000.0E/MSG/",
                            suffix="_MSG3_9_",
                            resolution=resolution
                            ),
              SatelliteData(longitude=-75.0,
                            limit={'left': 16, 'right': 688,
                                   'top': 70, 'bottom': 744},
                            rescale=ID,
                            base_url="075.0W/GOES/",
                            suffix="_GOES13_4_",
                            resolution=resolution
                            ),
              SatelliteData(longitude=-135.0,
                            limit={'left': 16, 'right': 688,
                                   'top': 70, 'bottom': 744},
                            rescale=ID,
                            base_url="135.0W/GOES/",
                            suffix="_GOES15_4_",
                            resolution=resolution
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
        mkdir.mkdir_p(self.tempdir)

        self.out_image = np.zeros(shape=(SatelliteData.outheight,
                                         SatelliteData.outwidth))

        weight_sum = np.zeros(shape=(SatelliteData.outheight,
                                     SatelliteData.outwidth))

        if self.nprocs == 1:
            i = 1
            for satellite in self.satellite_list:
                img = satellite.project()
                if debug:
                    self.imageDebug(i, img)
                i += 1
                weight_sum = weight_sum + img[1]
                self.out_image = self.out_image + (img[0] * img[1])
        else:
            from multiprocessing import Process, Queue
            pqs = []
            for satellite in self.satellite_list:
                satellite.outwidth = SatelliteData.outwidth
                satellite.outheight = SatelliteData.outheight
                q = Queue()
                p = Process(target=satellite.project, args=(q,))
                pqs.append((p, q))

            running = []
            i = 1
            j = 1
            while True:
                if len(running) < self.nprocs and len(pqs) > 0:
                    (p, q) = pqs.pop()
                    running.append((p, q))
                    j += 1
                    p.start()
                for (p, q) in running:
                    if not q.empty():
                        img = q.get()
                        if debug:
                            self.imageDebug(i, img)
                        weight_sum = weight_sum + img[1]
                        self.out_image = self.out_image + (img[0] * img[1])
                        running.remove((p, q))
                        i += 1
                if len(running) == 0 and len(pqs) == 0:
                    break
                time.sleep(0.01)

        self.out_image = self.out_image / weight_sum

        if debug:
            saveDebug(weight_sum,
                      os.path.join(self.tempdir, "weightsum.jpeg"))
            saveDebug(self.out_image,
                      os.path.join(self.tempdir, "test.jpeg"))

    def save_image(self, outdir, outfile):
        mkdir.mkdir_p(outdir)

        try:
            os.remove(os.path.join(outdir, outfile))
        except OSError:
            pass
        saveImage(self.out_image, os.path.join(outdir, outfile))

    def imageDebug(self, i, img):
        saveDebug(img[0],
                  os.path.join(self.tempdir, "test" +
                               repr(i) + ".jpeg"))
        saveDebug(img[1],
                  os.path.join(self.tempdir, "weighttest" +
                               repr(i) + ".jpeg"))
