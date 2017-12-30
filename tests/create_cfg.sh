#! /bin/bash

CFG_FILE=$HOME/.CreateCloudMap/CreateCloudMap.ini

echo "[Download]" > $CFG_FILE
echo "username = ${DUNDEE_USERNAME}" >> $CFG_FILE
echo "password = ${DUNDEE_PASSWORD}" >> $CFG_FILE
echo "tempdir = ${DUNDEE_TEMPDIR}" >> $CFG_FILE
echo "resolution = ${DUNDEE_RESOLUTION}" >> $CFG_FILE

echo "[xplanet]" >> $CFG_FILE
echo "destinationdir = xplanet/images" >> $CFG_FILE

echo "width = 4096" >> $CFG_FILE
echo "height = 2048" >> $CFG_FILE

echo "[processing]" >> $CFG_FILE
echo "nprocs = ${DUNDEE_NPROCS}" >> $CFG_FILE
echo "projection = ${DUNDEE_PROJECTION}" >> $CFG_FILE