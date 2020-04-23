#!/usr/bin/env python
# coding: utf-8

###**Script written by Barrett Sather for Airtonomy**###

import os
from subprocess import Popen, PIPE
import math
from PIL import Image

"""
utility convert_to_lat_lon

imgFile: Image with EXIF tags containing the target
pixelLoc: [x, y] location of the target in pixel space
"""

class imgToLatLon:
    def __init__(self, imgFile):
        # print("opening " + os.path.basename(imgFile))
        # print("------------")

        p = Popen('exiftool -GPSPosition -RelativeAltitude -FOV -GimbalYawDegree -GimbalPitchDegree -GPSLatitudeRef -GPSLongitudeRef {}'.format(imgFile).split(' '), stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate(b"input data that is passed to subprocess' stdin")

        if err!=b'':
            print("ERROR Reading EXIF tags: ({})".format(err))
            exit()

        # get image dimensions
        im = Image.open(imgFile)
        self.imgWidth, self.imgHeight = im.size

        # initialize lat, lon, alt, fov, roll, pitch, and yaw from the EXIF data
        lat_lon = output.decode().split('\n')[0].replace("'", '').replace('"', '').replace("deg", '').replace("N", '').replace("W", '').replace("S", '').replace("E", '').split(":")[1]
        lat = lat_lon.split(",")[0].split(" "); lon = lat_lon.split(",")[1].split(" ")
        lat = float(lat[1]) + float(lat[3])/60 + float(lat[4])/3600
        lon = float(lon[1]) + float(lon[3])/60 + float(lon[4])/3600
        self.alt = float(output.decode().split('\n')[1].split(":")[1].split(" ")[1])
        self.hfov = float(output.decode().split('\n')[2].split(":")[1].split(" ")[1])
        self.yaw = float(output.decode().split('\n')[3].split(":")[1].split(" ")[1])
        self.pitch = float(output.decode().split('\n')[4].split(":")[1].split(" ")[1])
        NRef = output.decode().split('\n')[5].split(":")[1].split(" ")[1]
        ERef = output.decode().split('\n')[6].split(":")[1].split(" ")[1]


        # Get in to the correct coord system
        if NRef == 'South\r':
            lat = -lat
        if ERef == 'West\r':
            lon = -lon
        # roll = 0
        self.lat = lat
        self.lon = lon


    def convert(self, pixelLoc):

        # get stored variables
        lat = self.lat
        lon = self.lon
        alt = self.alt
        hfov = self.hfov
        yaw = self.yaw
        pitch = self.pitch

        # constants for degrees -> radians and meters -> degrees
        dtor = math.pi / 180
        mtod = 1.0 / (110574 + 1120 * math.sin(lat*dtor))

        # find anngles to the pixel location in the image frame
        pixLeg = (self.imgWidth / 2) / math.tan(hfov/2 * dtor)
        xCenterLoc = pixelLoc[0] - (self.imgWidth / 2)
        hAddAngle = math.atan(xCenterLoc / pixLeg)
        yCenterLoc = (self.imgHeight / 2) - pixelLoc[1]
        vAddAngle = math.atan(yCenterLoc / pixLeg)

        #calculate unit pixel vector in absolute roll, pitch, and yaw
        vPitch = abs(pitch * dtor + vAddAngle) # assums drone gimbal is looking down
        vYaw = yaw * dtor + hAddAngle

        #draw the triangle on the Earth, assuming flat topography
        lGround = math.tan(vPitch) * alt
        # print("target found {} meters from drone ground position: ".format(round(lGround)))
        northing = math.cos(vYaw) * lGround # added northing in meters (can be negative)
        easting = math.sin(vYaw) * lGround # added easting in meters (can be negative)

        #convert to degrees and report back lat / lon of the bird.
        newLat = lat + (northing * mtod)
        newLon = lon + (easting * mtod / math.cos(lat*dtor))

        return newLat, newLon

# Example script
# imgFile = 'D:/Airtonomy/wildlife/data/DJI_0007_Flight4_45degree.JPG'
# pixelLoc = [400, 0]
# g = imgToLatLon(imgFile)
# newLat, newLon = g.convert(pixelLoc)
# print("target lat lon: ")
# print(newLat, newLon)
