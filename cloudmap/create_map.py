#!/usr/bin/env python

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

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


def saveImage(new_image, filename):
    """Save satellite image"""

    img = Image.fromarray(new_image).convert('RGB')
    img.save(filename)

def saveDebug(new_image, filename):
    import matplotlib
    matplotlib.use('AGG', warn=False)
    from pyresample import plot
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    
    bmap = plot.area_def2basemap(SatelliteData.pc(), resolution='c')
    bmap.drawcoastlines()
    bmap.drawmeridians(np.arange(-180, 180, 45))
    bmap.drawparallels(np.arange(-90, 90, 10))
    col = bmap.imshow(new_image, origin='upper', vmin=None, vmax=None, cmap = cm.Greys_r)
    plt.savefig(filename, bbox_inches='tight', pad_inches=0, dpi = 200)
    plt.close()

class SatelliteData:
    def __init__(self, longitude, extent, false_y, rescale, base_url, suffix):
        self.longitude = longitude
        self.extent    = extent
        self.false_y   = false_y
        self.rescale   = rescale
        self.base_url  = base_url
        self.suffix    = suffix
        self.rescale   = rescale
        self.filemodtime = 0
        
    def login(self, username, password):
        self.username = username
        self.password = password

    @staticmethod
    def curve(b):
        """Rescale the brightness values used for MTSAT2 satellite"""
        return np.minimum(b*255.0/193.0, 255)
    
    @staticmethod
    def ID(b):
        """Identity function"""
        return b

    def set_time(self, dt, tempdir=""):
        self.dt = datetime.datetime(dt.year, dt.month, dt.day, dt.hour/3*3, 0, 0)
        day = self.dt.strftime("%d").lstrip("0")
        month = self.dt.strftime("%m").lstrip("0")
        hour  = self.dt.strftime("%H").lstrip("0")
        str1 = self.dt.strftime("%Y/")+ month + "/" + day + "/" + hour + "00/"
        str2 = self.dt.strftime("%Y_") + month + "_" + day + "_" + hour + "00"
        self.url      = self.base_url + str1 + str2 + self.suffix
        self.filename = os.path.join(tempdir, str2 + self.suffix)
            
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
        """Return the first row index not containing the white border at the top"""
    
        look  = False
        start = 3
        i = start
        left  = 10
        right = img.shape[0] - 10
        for r in img[start:]:
            m = np.amin(r[left:right])
    #        print m
            if (look and m < 255):
                return i
            elif (not look and m == 255):
                look = True
            i = i + 1
        return 0
    
    def cut_borders(self):
        """Remove the white border of a satellite images (including text)"""
    
        x1 = self.findStartIndex(self.data)
        self.data = self.data[x1:,:]
        self.data = self.data[::-1]
        x2 = self.findStartIndex(self.data)
        self.data = self.data[x2:,:]
        self.data = self.data[::-1]
    
        self.data = self.data.T
        x1 = self.findStartIndex(self.data)
        self.data = self.data[x1:,:]
        self.data= self.data[::-1]
        x2 = self.findStartIndex(self.data)
        self.data = self.data[x2:,:]
        self.data = self.data[::-1]
        return self.data.T
    
    @staticmethod
    def pc():
        proj_dict = {'proj': 'eqc'}
        area_extent =(-20037508.34, -10018754.17, 20037508.34, 10018754.17)
        x_size = 2048
        y_size = 1024
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
        area_extent =(-self.extent, -self.extent,
                      self.extent, self.extent)
        area = geometry.AreaDefinition('geo', 'geostat', 'geo', proj_dict, x_size,
                                       y_size, area_extent)
        dataIC = image.ImageContainerQuick(self.data, area)
        
        #msg_con_nn = image.ImageContainerNearest(data, area, radius_of_influence=50000)
        dataResampled = dataIC.resample(SatelliteData.pc())
        dataResampledImage = self.rescale(dataResampled.image_data)
    
        dataResampledImage[0:90, :] = dataResampledImage[180:90:-1, :]
        dataResampledImage[1024-90:1024, :] = dataResampledImage[1024-90:1024-180:-1, :]

        width = 55
        weight = np.array([max((width - min([abs(self.longitude - x),
                                             abs(self.longitude - x + 360),
                                             abs(self.longitude - x - 360)]))/180,
                               1e-7) for x in np.linspace(-180, 180, dataResampled.shape[1])])
        return np.array([dataResampledImage, np.tile(weight, (dataResampled.shape[0], 1))])


def main():
    satellite_list = (
                      SatelliteData(145.0, 5433878.562*1.01, 50000,
                                    SatelliteData.curve,
                                    "http://www.sat.dundee.ac.uk/xrit/145.0E/MTSAT/",
                                    "_MTSAT2_4_S2.jpeg"
                                    ),
                      SatelliteData(57.0, 5568742.4*0.97, 0,
                                    SatelliteData.ID,
                                    "http://www.sat.dundee.ac.uk/xrit/057.0E/MET/",
                                    "_MET7_2_S2.jpeg"
                                    ),
                      SatelliteData(0.0, 5433878.562, 0,
                                    SatelliteData.ID,
                                    "http://www.sat.dundee.ac.uk/xrit/000.0E/MSG/",
                                    "_MSG3_9_S2.jpeg"
                                    ),
                      SatelliteData(-75.0, 5433878.562, 0,
                                    SatelliteData.ID,
                                    "http://www.sat.dundee.ac.uk/xrit/075.0W/GOES/",
                                    "_GOES13_4_S2.jpeg"
                                    ),
                      SatelliteData(-135.0, 5433878.562, 0,
                                    SatelliteData.ID,
                                    "http://www.sat.dundee.ac.uk/xrit/135.0W/GOES/",
                                    "_GOES15_4_S2.jpeg"
                                    ),
                      )

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="store intermediate results",
                        action="store_true")
    parser.add_argument("-c", "--conf_file", help="Specify config file", 
                        metavar="FILE", default="cloudmap.ini")
    parser.add_argument("-f", "--force", help="Force to recreate cloud map",
                        action="store_true")
    args = parser.parse_args()
    config = ConfigParser.SafeConfigParser()
    config.read([args.conf_file])
    
    username = dict(config.items("Download"))['username']
    password = dict(config.items("Download"))['password']
    tempdir  = dict(config.items("Download"))['tempdir']
    outdir   = dict(config.items("xplanet"))['destinationdir']
    
    images = np.empty(shape=(5, 2, 1024, 2048))
    
    dt = datetime.datetime.utcnow()
    max_tries = 10
    
    for _ in range(max_tries):
        found_all = True
    
        for satellite in satellite_list:
            satellite.login(username, password)
            satellite.set_time(dt, tempdir)
            found_all = found_all and satellite.check_for_image()
            
        if found_all: break
        dt = dt - datetime.timedelta(hours = 3)

    if not found_all:
        sys.exit("Cannot download (all) satellite images!")

    print "Download image date/time: ", satellite_list[0].dt.strftime("%Y-%m-%d %H:00 UTC")
    
    mkdir_p(tempdir)

    latest_download = 0    
    for satellite in satellite_list:
        print "Satellite file: ", satellite.filename
        satellite.download_image()
        latest_download = max(latest_download, satellite.filemodtime)
        
    if (
        not args.force and
        os.path.isfile(os.path.join(outdir, "clouds_2048.jpg")) and 
        (os.path.getmtime(os.path.join(outdir, "clouds_2048.jpg")) > latest_download)
        ):
        sys.exit(0)
        
    i = 1
    for satellite in satellite_list:
        img = satellite.project()
        if args.debug:
            saveDebug(img[0],
                      os.path.join(tempdir, "test" + `i` + ".jpeg"))
            saveDebug(np.array(img[1]*255, 'uint8'),
                      os.path.join(tempdir, "weighttest" + `i` + ".jpeg"))
        images[i-1] = img
        i += 1
    
    weight_sum = np.sum(images[:, 1], axis = 0)
    if args.debug: saveDebug(np.array(weight_sum*255, 'uint8'), os.path.join(tempdir, "weightsum.jpeg"))
    new_image = np.sum(images[:, 0] * images[:, 1], axis = 0)/weight_sum
    
    mkdir_p(outdir)

    try:
        os.remove(os.path.join(outdir, "clouds_2048.jpg"))
    except OSError:
        pass
    saveImage(new_image, os.path.join(outdir, "clouds_2048.jpg"))
    if args.debug: saveDebug(new_image, 
                             os.path.join(tempdir,"test.jpeg"))
    print "finished"

if __name__ == '__main__':
    main()