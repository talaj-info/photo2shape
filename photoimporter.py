# -*- coding: utf-8 -*-

"""
***************************************************************************
    photoimporter.py
    ---------------------
    Date                 : November 2014
    Copyright            : (C) 2010-2014 by Alexander Bruy
    Email                : alexander dot bruy at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Alexander Bruy'
__date__ = 'November 2014'
__copyright__ = '(C) 2010-2014, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

import exifread

from PyQt4.QtCore import *

from qgis.core import *


class PhotoImporter(QObject):

    importError = pyqtSignal(unicode)
    importMessage = pyqtSignal(unicode)
    photoProcessed = pyqtSignal(int)
    importFinished = pyqtSignal()

    def __init__(self):
        QObject.__init__(self)

    def setPhotosDirectory(self, directory):
        self.directory = directory

    def setOutputPath(self, filePath):
        self.shapePath = filePath

    def setEncoding(self, encoding):
        self.encoding = encoding

    def setRecurseDirs(self, recurse):
        self.recurse = recurse

    def setAppendFile(self, append):
        self.append = append

    def importPhotos(self):
        if self.append:
            layer = self._openShapefile()
        else:
            layer = self._newShapefile()

        if layer is None:
            self.importError.emit(self.tr('Unable to open or create layer.'))

        provider = layer.dataProvider()
        fields = layer.pendingFields()

        photos = []
        for root, dirs, files in os.walk(self.directory):
            photos.extend(os.path.join(root, fName) for fName in files
                          if fName.lower().endswith(('.jpg', '.jpeg')))
            if not self.recurse:
                break

        if len(photos) == 0:
            self.importError.emit(self.tr('No images found in directory.'))

        total = 100.0 / len(photos)

        ft = QgsFeature()
        ft.setFields(fields)
        for count, fName in enumerate(photos):
            with open(fName, 'rb') as imgFile:
                tags = exifread.process_file(imgFile, details=False)

            if not tags.viewkeys() & {'GPS GPSLongitude', 'GPS GPSLatitude'}:
                self.importMessage.emit(
                    self.tr('Skipping file %s: there are no GPS tags in it.') % fName)
                self.photoProcessed.emit(int(count * total))
                continue

            # Start processing tags
            longitude, latitude = self._extractCoordinates(tags)
            if longitude is None:
                self.importMessage.emit(
                    self.tr('Skipping file %s: there are no GPS fix data.') % fName)
                self.photoProcessed.emit(int(count * total))
                continue

            altitude = self._extractAltitude(tags)
            north, azimuth = self._extractDirection(tags)
            gpsDate = self._extracrGPSDateTime(tags)
            imgDate = self._extractImageDateTime(tags)
            del tags

            # Write feature to layer
            ft.setGeometry(
                QgsGeometry.fromPoint(QgsPoint(longitude, latitude)))
            ft['filepath'] = fName
            ft['filename'] = os.path.basename(fName)
            ft['longitude'] = longitude
            ft['latitude'] = latitude
            ft['altitude'] = altitude
            ft['north'] = north
            ft['azimuth'] = azimuth
            ft['gps_date'] = gpsDate
            ft['img_date'] = imgDate
            provider.addFeatures([ft])
            self.photoProcessed.emit(int(count * total))

        self.importFinished.emit()

    def _openShapefile(self):
        layer = QgsVectorLayer(
            self.shapePath, QFileInfo(self.shapePath).baseName(), 'ogr')

        return layer

    def _newShapefile(self):
        fields = QgsFields()
        fields.append(QgsField('filepath', QVariant.String, '', 255))
        fields.append(QgsField('filename', QVariant.String, '', 255))
        fields.append(QgsField('longitude', QVariant.Double, '', 20, 7))
        fields.append(QgsField('latitude', QVariant.Double, '', 20, 7))
        fields.append(QgsField('altitude', QVariant.Double, '', 20, 7))
        fields.append(QgsField('north', QVariant.String, '', 1))
        fields.append(QgsField('azimuth', QVariant.Double, '', 20, 7))
        fields.append(QgsField('gps_date', QVariant.String, '', 255))
        fields.append(QgsField('img_date', QVariant.String, '', 255))

        crs = QgsCoordinateReferenceSystem(4326)
        writer = QgsVectorFileWriter(
            self.shapePath, self.encoding, fields, QGis.WKBPoint, crs)
        del writer

        layer = QgsVectorLayer(
            self.shapePath, QFileInfo(self.shapePath).baseName(), 'ogr')

        return layer

    def _extractCoordinates(self, tags):
        # Some devices (e.g. with Android 1.6) write tags in non standard
        # way as decimal degrees in ASCII field
        dataType = tags['GPS GPSLongitude'].field_type
        typeName = exifread.tags.FIELD_TYPES[dataType][2]
        if typeName == 'ASCII':
            lon = round(float(tags['GPS GPSLongitude'].values), 7)
            lat = round(float(tags['GPS GPSLatitude'].values), 7)
            return lon, lat

        # Sometimes tags present by filled with zeros
        if tags['GPS GPSLongitude'].printable == '[0/0, 0/0, 0/0]':
            return None, None

        # Longitude direction will be either "E" or "W"
        lonDirection = tags['GPS GPSLongitudeRef'].printable
        # Coordinates stored as list of degrees, minutes and seconds
        v = tags['GPS GPSLongitude'].values
        ddLon = v[0].num if v[0].den == 1 else (v[0].num * 1.0) / v[0].den
        mmLon = v[1].num if v[1].den == 1 else (v[1].num * 1.0) / v[1].den
        ssLon = v[2].num if v[2].den == 1 else (v[2].num * 1.0) / v[2].den

        # Latitude direction will be either "N" or "S"
        latDirection = tags['GPS GPSLatitudeRef'].printable
        # Coordinates stored as list of degrees, minutes and seconds
        v = tags['GPS GPSLatitude'].values
        ddLat = v[0].num if v[0].den == 1 else (v[0].num * 1.0) / v[0].den
        mmLat = v[1].num if v[1].den == 1 else (v[1].num * 1.0) / v[1].den
        ssLat = v[2].num if v[2].den == 1 else (v[2].num * 1.0) / v[2].den

        # Convert to decimal degrees
        mmLon = mmLon / 60.0 if mmLon != 0.0 else 0.0
        ssLon = ssLon / 3600.0 if ssLon != 0.0 else 0.0
        lon = round(ddLon + mmLon + ssLon, 7)

        mmLat = mmLat / 60.0 if mmLat != 0.0 else 0.0
        ssLat = ssLat / 3600.0 if ssLat != 0.0 else 0.0
        lat = round(ddLat + mmLat + ssLat, 7)

        # Apply direction
        if lonDirection == 'W':
            lon = 0 - lon
        if latDirection == 'S':
            lat = 0 - lat

        return lon, lat

    def _extractAltitude(self, tags):
        if 'GPS GPSAltitude' not in tags:
            return None

        # Some devices (e.g. with Android 1.6) write tags in non standard
        # way as ASCII field. Also they don't write GPS GPSAltitudeRef tag
        dataType = tags['GPS GPSAltitude'].field_type
        typeName = exifread.tags.FIELD_TYPES[dataType][2]
        if typeName == 'ASCII':
            altitude = tags['GPS GPSAltitude'].values
            return round(float(altitude), 7)

        if 'GPS GPSAltitudeRef' not in tags:
            return None

        # Reference will be either 0 or 1
        reference = tags['GPS GPSAltitudeRef'].values[0]
        v = tags['GPS GPSAltitude'].values[0]
        altitude = float(v.num) if v.den == 1 else (v.num * 1.0) / v.den

        # Apply reference
        if reference == 1:
            altitude = 0 - altitude

        return round(altitude, 7)

    def _extractDirection(self, tags):
        if 'GPS GPSImgDirection' not in tags:
            return None, None

        # Sometimes tag present by filled with zeros
        if tags['GPS GPSImgDirection'].printable == '[0/0, 0/0, 0/0]':
            return None, None

        # Reference will be either "T" or "M"
        reference = tags['GPS GPSImgDirectionRef'].values
        v = tags['GPS GPSImgDirection'].values[0]
        azimuth = float(v.num) if v.den == 1 else (v.num * 1.0) / v.den

        return reference, round(azimuth, 7)

    def _extracrGPSDateTime(self, tags):
        imgDate = None
        if 'GPS GPSDate' in tags:
            imgDate = tags['GPS GPSDate'].values

        if 'GPS GPSTimeStamp' in tags:
            # Some devices (e.g. with Android 1.6) write tags in non standard
            # way as ASCII field. Also they don't write GPS GPSDate tag
            dataType = tags['GPS GPSTimeStamp'].field_type
            typeName = exifread.tags.FIELD_TYPES[dataType][2]
            if typeName == 'ASCII':
                return tags['GPS GPSTimeStamp'].values
            else:
                v = tags['GPS GPSTimeStamp'].values
                imgTime = '{:0>2}:{:0>2}:{:0>2}'.format(v[0], v[1], v[2])
                if imgDate is None:
                    return imgTime
                else:
                    return '{} {}'.format(imgDate, imgTime)

        return None

    def _extractImageDateTime(self, tags):
        if 'Image DateTime' in tags:
            return tags['Image DateTime'].values

        return None
