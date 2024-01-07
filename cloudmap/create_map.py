#!/usr/bin/env python
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import argparse
import configparser
import os
import timeit
import logging

from .__init__ import CloudMap, __version__


def main():
    """
    Create world satellite image using the latest images from the
    Satellites server
    """

    logging.basicConfig(format='%(name)s:%(levelname)5s: %(message)s')
    logger = logging.getLogger('create_map_logger')

    tic = timeit.default_timer()
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="debug outputs",
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
    config = configparser.ConfigParser(
        {'width': '2048',
         'height': '1024',
         'destinationfile': 'clouds_2048.jpg',
         }
        )
    config.read([args.conf_file])

    outdir = config.get("xplanet", 'destinationdir')
    outfile = config.get("xplanet", 'destinationfile')

    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    outwidth = int(config.get("xplanet", 'width'))
    outheight = int(config.get("xplanet", 'height'))

    satellite_list = CloudMap(outwidth, outheight)

    satellite_list.download(outdir, outfile, args.force)

    toc = timeit.default_timer()

    logger.info("finished in {:.1f} s".format((toc - tic)))


if __name__ == '__main__':
    main()
