cloudmap
========

Python script to create a cloud map for xplanet using satellite images from the [Dundee Satellite Receiving Station, Dundee University, UK](http://www.sat.dundee.ac.uk/)

[xplanet](http://xplanet.sourceforge.net/) can use a cloud map to make the earth look more pretty. 

There is a free service which create one such cloud map per day. Due to a temporary unavailability of that service I created this script to automatically download the necessary geostationary images from the [Dundee Satellite Receiving Station, Dundee University, UK](http://www.sat.dundee.ac.uk/). To use this service you need an account there (which is free). Also a new cload map can be created every three hours.

Set your login information in the configuration file (default name `cloudmap.ini`):
```
[Download]
username = user
password = secret
tempdir = images

[xplanet]
destinationdir = xplanet/images
```
`tempdir` specifies the directory where the downloaded images (and if enabled by the command line switch `--debug` or `-d`) intermediate debug images are stored. `destinationdir` specifies the directory where the output `clouds_2048.jpg` is saved.

To see all command line options of the script use `--help`:
```
$ python create_map.py --help
usage: create_map.py [-h] [-d] [-c FILE]

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           store intermediate results
  -c FILE, --conf_file FILE
                        Specify config file
```  