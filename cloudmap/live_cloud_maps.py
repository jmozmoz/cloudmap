from pathlib import Path
import requests
from datetime import datetime, timezone
from dateutil import parser
import json
import os
import logging


class CloudMap(object):

    """
    Class to download and process the could map from clouds.matteason.co.uk
    """

    available_resolutions = [
        (1024, 512),
        (2048, 1024),
        (4096, 2048),
        (8192, 4096),
    ]

    def __init__(self, outwidth, outheight):
        """
        Args:
            * outwidth:
                width of the downloaded cloud map
            * outheight:
                height of the downloaded cloud map
            * debug
                print debug outputs
        """

        self.logger = logging.getLogger('create_map_logger')

        if (outwidth, outheight) not in CloudMap.available_resolutions:
            self.logger.error(
                f'{outwidth}, {outheight} no valid resolution!\n' +
                f'resolutions available: {CloudMap.available_resolutions}'
            )
            raise ValueError(f'{outwidth}, {outheight} no valid resolution')

        self._url = (
            'https://clouds.matteason.co.uk/images/' +
            f'{outwidth}x{outheight}/clouds.jpg'
        )

    def download(self, outdir, outfile, force):
        """
        Download cloud map

        Args:
            * outdir:
                Directory the image should be saved in
            * outfile:
                Filename of the image
            * force:
                Force reloading the image
        """

        Path(outdir).mkdir(parents=True, exist_ok=True)

        response = requests.head(self._url, allow_redirects=True, timeout=10)
        self.logger.debug(json.dumps(dict(response.headers), indent=4))

        out_path = outdir / Path(outfile)
        new_time = parser.parse(response.headers['last-modified'])

        if force:
            self.logger.info(f'{out_path} forcefully downloaded')
            out_path.unlink(missing_ok=True)
            self._download_image(self._url, out_path, new_time)
        elif not out_path.exists():
            self.logger.debug(f'{out_path} not found')
            self._download_image(self._url, out_path, new_time)
        else:
            old_time = datetime.fromtimestamp(
                out_path.stat().st_mtime, tz=timezone.utc
            )
            if new_time > old_time:
                out_path.unlink()
                self.logger.debug(f'{out_path} too old')
                self._download_image(self._url, out_path, new_time)
            else:
                self.logger.info(f'{out_path} is new enough')

    def _download_image(self, t, out_file, d):
        r = requests.get(t, allow_redirects=True, timeout=20)
        self.logger.debug(f'{t}: length: {len(r.content)}')
        with open(out_file, 'wb') as f:
            f.write(r.content)
        os.utime(out_file, (d.timestamp(), d.timestamp()))
        r.close()
        self.logger.debug(f'downloaded {out_file}')
