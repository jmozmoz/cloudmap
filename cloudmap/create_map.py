#!/usr/bin/env python
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import argparse
import ConfigParser
import os
import sys

from satellite import SatelliteData
from dundee import Dundee
from _version import __version__


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
    parser.add_argument('-V', '--version', action='version',
                    version=__version__)
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

    satellite_list = Dundee(resolution, username, password,
                            tempdir)
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

    print("finished")

if __name__ == '__main__':
    main()
