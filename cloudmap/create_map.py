#!/usr/bin/env python
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import argparse
import configparser
import os
import sys
import time

from .__init__ import Dundee, SatelliteData, __version__


def main():
    """
    Create world satellite image using the latest images from the
    Dundee server
    """

    tic = time.clock()
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="store intermediate results",
                        action="store_true")
    parser.add_argument("-c", "--conf_file", help="Specify config file",
                        metavar="FILE",
                        default=os.path.expanduser(
                           "~/.CreateCloudMap/CreateCloudMap.ini"))
    parser.add_argument("-f", "--force", help="Force to recreate cloud map",
                        action="store_true")
    parser.add_argument('-V', '--version', action='version',
                    version=__version__)
    args = parser.parse_args()
    config = configparser.SafeConfigParser(
        {'width': '2048',
         'height': '1024',
         'destinationfile': 'clouds_2048.jpg',
         'resolution': 'medium',
         'purge': 'false',
         'nprocs': '1',
         'projection': 'pyresample'
         }
        )
    config.read([args.conf_file])

    username = config.get("Download", 'username')
    password = config.get("Download", 'password')
    tempdir = config.get("Download", 'tempdir')
    resolution = config.get("Download", 'resolution')
    purge = config.get("Download", 'purge').lower() == 'true'

    outdir = config.get("xplanet", 'destinationdir')
    outfile = config.get("xplanet", 'destinationfile')

    try:
        nprocs = int(config.get("processing", 'nprocs'))
    except (configparser.NoSectionError, configparser.NoOptionError):
        nprocs = 1

    try:
        SatelliteData.projection_method =\
            config.get("processing", 'projection')
    except (configparser.NoSectionError, configparser.NoOptionError):
        SatelliteData.projection_method = 'pyresample'

    if SatelliteData.projection_method not in ['cartopy', 'pyresample']:
        print("Incorrect projection library setting:",
              SatelliteData.projection_method)
        print("Use either pyresample or cartopy")
        sys.exit(1)

    SatelliteData.outwidth = int(config.get("xplanet", 'width'))
    SatelliteData.outheight = int(config.get("xplanet", 'height'))

    satellite_list = Dundee(resolution, username, password,
                            tempdir, nprocs)
    dt = satellite_list.find_latest()

    print("Download image date/time: ",
          dt.strftime("%Y-%m-%d %H:00 UTC"))

    latest_download = satellite_list.download(purge)

    # Stop here if downloaded satellite images are older than
    # current cloud image
    if (
        not args.force and
        os.path.isfile(os.path.join(outdir, outfile)) and
        (os.path.getmtime(os.path.join(outdir, outfile))
         > latest_download)
    ):
        sys.exit(0)

    satellite_list.overlay(args.debug)
    satellite_list.save_image(outdir, outfile)

    toc = time.clock()

    print("finished in {:.1f} s".format((toc - tic)))

if __name__ == '__main__':
    main()
