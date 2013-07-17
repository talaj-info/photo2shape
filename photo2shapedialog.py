# -*- coding: utf-8 -*-

#******************************************************************************
#
# Photo2Shape
# ---------------------------------------------------------
# Create a point shapefile from a set of geotagged images
#
# Based on ImagesToShape plugin (C) 2009 by Tim Sutton
#
# Copyright (C) 2010-2013 Alexander Bruy (alexander.bruy@gmail.com)
#
# This source is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This code is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# A copy of the GNU General Public License is available on the World Wide Web
# at <http://www.gnu.org/copyleft/gpl.html>. You can also obtain it by writing
# to the Free Software Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA.
#
#******************************************************************************


from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

import os.path
import re
import EXIF

import photo2shape_utils as utils

from ui_photo2shapedialogbase import Ui_Photo2ShapeDialog


class Photo2ShapeDialog(QDialog, Ui_Photo2ShapeDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)

        self.photoProcessingThread = None

        self.okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        self.closeButton = self.buttonBox.button(QDialogButtonBox.Close)

        self.selectInputDirButton.clicked.connect(self.selectInputDir)
        self.selectOutputFileButton.clicked.connect(self.selectOutputFile)

        self.manageGui()

    def manageGui(self):
        self.addToCanvasCheck.setChecked(utils.addToCanvas())

    def selectInputDir(self):
        inputDir = QFileDialog.getExistingDirectory(self,
                                                    self.tr("Select directory with images"),
                                                    utils.lastPhotosDir()
                                                   )
        if inputDir == "":
            return

        workDir = QDir(inputDir)
        workDir.setFilter(QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot)
        nameFilter = ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG"]
        workDir.setNameFilters(nameFilter)
        self.inputFiles = workDir.entryList()
        if len(self.inputFiles) == 0:
            QMessageBox.warning(self,
                                self.tr("No images found"),
                                self.tr("There are no supported images in this directory. Please select another one.")
                               )
            self.inputFiles = None
            return

        utils.setLastPhotosDir(inputDir)
        self.progressBar.setRange(0, len(self.inputFiles))
        self.inputDirEdit.setText(inputDir)

    def selectOutputFile(self):
        # prepare dialog parameters
        settings = QSettings()
        lastDir = utils.lastShapefileDir()
        shpFilter = self.tr("Shapefiles (*.shp *.SHP)")

        fileDialog = QgsEncodingFileDialog(self,
                                           self.tr("Select output shapefile"),
                                           lastDir,
                                           shpFilter,
                                           ""
                                          )
        fileDialog.setDefaultSuffix(u"shp")
        fileDialog.setFileMode(QFileDialog.AnyFile)
        fileDialog.setAcceptMode(QFileDialog.AcceptSave)
        fileDialog.setConfirmOverwrite(True)

        if not fileDialog.exec_() == QDialog.Accepted:
            return

        outputFile = fileDialog.selectedFiles()
        self.outputEncoding = fileDialog.encoding()

        utils.setLastShapefileDir(outputFile[0])
        self.outputFileEdit.setText(outputFile[0])

    def reject(self):
        utils.setAddToCanvas(self.addToCanvasCheck.isChecked())

        QDialog.reject(self)

    def accept(self):
        outFileName = self.outputFileEdit.text()

        if outFileName == "":
            QMessageBox.warning(self,
                                self.tr("Wrong output file"),
                                self.tr("Output file is improperly defined.\nPlease enter a valid filename and try again.")
                               )
            return

        outFile = QFile(outFileName)
        if outFile.exists():
            if not QgsVectorFileWriter.deleteShapeFile(outFileName):
                QMessageBox.warning(self,
                                    self.tr("Delete error"),
                                    self.tr("Can't delete file %s") % (outFileName)
                                   )
                return

        utils.setAddToCanvas(self.addToCanvasCheck.isChecked())
        baseDir = self.inputDirEdit.text()

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.okButton.setEnabled(False)

        self.photoProcessingThread = ImageProcessingThread(baseDir,
                                                           self.inputFiles,
                                                           outFileName,
                                                           self.outputEncoding
                                                          )
        self.photoProcessingThread.photoProcessed.connect(self.photoProcessed)
        self.photoProcessingThread.processingFinished.connect(self.processingFinished)
        self.photoProcessingThread.processingInterrupted.connect(self.processingInterrupted)

        self.closeButton.setText(self.tr("Cancel"))
        self.buttonBox.rejected.disconnect(self.reject)
        self.closeButton.clicked.connect(self.stopProcessing)

        self.photoProcessingThread.start()

    def photoProcessed(self):
        self.progressBar.setValue(self.progressBar.value() + 1)

    def processingFinished(self, errorsList, hasOutput):
        self.stopProcessing()

        if not hasOutput:
            QMessageBox.warning(self,
                                self.tr("Photo2Shape"),
                                self.tr("There are no geotagged photos in selected directory.\nShapefile was not created.")
                               )
            self.restoreGUI()
            return

        if len(errorsList) > 0:
            msg = self.tr("The following files were not added to shapefile because of errors: <br><br>") + "<br><br>".join(errorsList)
            dlgError = QErrorMessage(self)
            dlgError.showMessage(msg)

        self.writeQml()
        if self.addToCanvasCheck.isChecked():
            self.addLayerToCanvas()

        self.restoreGUI()

    def processingInterrupted(self):
        self.restoreGUI()

    def stopProcessing(self):
        if self.photoProcessingThread is not None:
            self.photoProcessingThread.stop()
            self.photoProcessingThread = None

    def restoreGUI(self):
        self.progressBar.setValue(0)
        QApplication.restoreOverrideCursor()
        self.buttonBox.rejected.connect(self.reject)
        self.closeButton.setText(self.tr("Close"))
        self.okButton.setEnabled(True)

    def addLayerToCanvas(self):
        layerPath = self.outputFileEdit.text()
        newLayer = QgsVectorLayer(layerPath, QFileInfo(layerPath).baseName(), "ogr")

        if newLayer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(newLayer)
        else:
            QMessageBox.warning(self,
                                self.tr("Photo2Shape"),
                                self.tr("Error loading output shapefile:\n%s") % (layerPath)
                               )

    def writeQml(self):
        if not QFile(self.outputFileEdit.text()).exists():
            return

        sourceQml = os.path.join(os.path.dirname(__file__), "photos.qml")
        sourceFile = QFile(sourceQml)
        outputQml = self.outputFileEdit.text().replace(".shp", ".qml")
        outputFile = QFile(outputQml)
        if outputFile.exists():
            res = QMessageBox.question(self,
                                       self.tr("QML exists"),
                                       self.tr("QML file %s already exists. Overwrite?") % (outputQml),
                                       QMessageBox.Yes | QMessageBox.No
                                      )
            if res != QMessageBox.Yes:
                return
            outputFile.remove()

        if not sourceFile.copy(outputQml):
            QMessageBox.warning(self,
                                self.tr("QML error"),
                                self.tr("Can't write QML file")
                               )


def getCoordinates(tags):
    exifTags = tags

    # some devices (e.g. with Android 1.6) write tags in non standard way
    # as decimal degrees in ASCII field
    if EXIF.FIELD_TYPES[exifTags["GPS GPSLongitude"].field_type][2] == 'ASCII':
        strLon = str(exifTags["GPS GPSLongitude"])
        strLat = str(exifTags["GPS GPSLatitude"])
        lon = round(float(strLon), 7)
        lat = round(float(strLat), 7)
        return (lon, lat)

    # get the position info as reported by EXIF
    lonDirection = None
    lonDegrees = None
    lonMinutes = None
    lonSeconds = None
    latDirection = None
    latDegrees = None
    latMinutes = None
    latSeconds = None

    # longitude direction will be either "E" or "W"
    lonDirection = str(exifTags["GPS GPSLongitudeRef"])
    # EXIF returns degrees, minutes and seconds in list, so we need to split it
    longitude = str(exifTags["GPS GPSLongitude"])[1:-1].split(", ")
    lonDegrees = longitude[0]
    lonMinutes = longitude[1]
    lonSeconds = longitude[2]

    # latitude direction will be either "N" or "S"
    latDirection = str(exifTags["GPS GPSLatitudeRef"])
    # EXIF returns degrees, minutes and seconds in list, so we need to split it
    latitude = str(exifTags["GPS GPSLatitude"])[1:-1].split(", ")
    latDegrees = latitude[0]
    latMinutes = latitude[1]
    latSeconds = latitude[2]

    # get the degree, minutes and seconds values
    regexp = re.compile("^[0-9]*")
    lonDegreesFloat = float(regexp.search(str(lonDegrees)).group())
    lonMinutesFloat = float(regexp.search(str(lonMinutes)).group())
    lonSecondsFloat = float(regexp.search(str(lonSeconds)).group())
    latDegreesFloat = float(regexp.search(str(latDegrees)).group())
    latMinutesFloat = float(regexp.search(str(latMinutes)).group())
    latSecondsFloat = float(regexp.search(str(latSeconds)).group())

    # divide the values by the divisor if neccessary
    regexp = re.compile("[0-9]*$")
    if lonDegrees.find("/") == -1:
        myLonDegrees = lonDegreesFloat
    else:
        myLonDegrees = lonDegreesFloat / float(regexp.search(str(lonDegrees)).group())
    if lonMinutes.find("/") == -1:
        myLonMinutes = lonMinutesFloat
    else:
        myLonMinutes = lonMinutesFloat / float(regexp.search(str(lonMinutes)).group())
    if lonSeconds.find("/") == -1:
        myLonSeconds = lonSecondsFloat
    else:
        myLonSeconds = lonSecondsFloat / float(regexp.search(str(lonSeconds)).group())

    if latDegrees.find("/") == -1:
        myLatDegrees = latDegreesFloat
    else:
        myLatDegrees = latDegreesFloat / float(regexp.search(str(latDegrees)).group())
    if latMinutes.find("/") == -1:
        myLatMinutes = latMinutesFloat
    else:
        myLatMinutes = latMinutesFloat / float(regexp.search(str(latMinutes)).group())
    if latSeconds.find("/") == -1:
        myLatSeconds = latSecondsFloat
    else:
        myLatSeconds = latSecondsFloat / float(regexp.search(str(latSeconds)).group())

    # we now have degrees, decimal minutes and decimal seconds, so convert to decimal degrees
    lon = round(myLonDegrees + (myLonMinutes / 60) + (myLonSeconds / 3600), 7)
    lat = round(myLatDegrees + (myLatMinutes / 60) + (myLatSeconds / 3600), 7)

    # use a negative sign as needed
    if lonDirection == "W":
        lon = 0 - lon
    if latDirection == "S":
        lat = 0 - lat

    return (lon, lat)


def getAltitude(tags):
    exifTags = tags

    if "GPS GPSAltitude" not in exifTags:
        return None

    # some devices (e.g. with Android 1.6) write tags in non standard way
    # as decimal degrees in ASCII field also they don't write
    # GPS GPSAltitudeRef tag
    if EXIF.FIELD_TYPES[exifTags["GPS GPSAltitude"].field_type][2] == 'ASCII':
        alt = str(exifTags["GPS GPSAltitude"])
        return round(float(alt), 7)

    if "GPS GPSAltitudeRef" not in exifTags:
        return None

    # altitude
    altDirection = exifTags["GPS GPSAltitudeRef"]
    altitude = str(exifTags["GPS GPSAltitude"])

    # get altitude value
    regexp = re.compile("^[0-9]*")
    altitudeFloat = float(regexp.search(str(altitude)).group())

    # divide the value by the divisor if neccessary
    regexp = re.compile("[0-9]*$")
    if altitude.find("/") == -1:
        myAltitude = altitudeFloat
    else:
        myAltitude = altitudeFloat / float(regexp.search(str(altitude)).group())

    # use negative sign as needed
    if altDirection == 1:
        myAltitude = 0 - myAltitude

    return round(myAltitude, 7)


def getGPSDateTime(tags):
    exifTags = tags

    imgDate = None
    imgTime = None

    if "GPS GPSDate" in exifTags:
        imgDate = str(exifTags["GPS GPSDate"])

    if "GPS GPSTimeStamp" in exifTags:
        # some devices (e.g. Android) save this tag in non-standard way
        if EXIF.FIELD_TYPES[exifTags["GPS GPSTimeStamp"].field_type][2] == 'ASCII':
            return str(exifTags["GPS GPSTimeStamp"])
        else:
            tmp = str(exifTags["GPS GPSTimeStamp"])[1:-1].split(", ")
            imgTime = tmp[0] + ":" + tmp[1] + ":" + tmp[2]
            if imgDate is None:
                return imgTime
            return imgDate + " " + imgTime

    return None


def getImageDateTime(tags):
    exifTags = tags

    if "Image DateTime" in exifTags:
        return str(exifTags["Image DateTime"])

    return None


def getDirection(tags):
    exifTags = tags

    if "GPS GPSImgDirection" not in exifTags:
        return None

    myAzimuth = str(exifTags["GPS GPSImgDirectionRef"])
    direction = str(exifTags["GPS GPSImgDirection"])

    # get direction value
    regexp = re.compile("^[0-9]*")
    directionFloat = float(regexp.search(str(direction)).group())

    # divide the value by the divisor if neccessary
    regexp = re.compile("[0-9]*$")
    if direction.find("/") == -1:
        myDirection = directionFloat
    else:
        myDirection = directionFloat / float(regexp.search(str(direction)).group())

    return (myAzimuth, round(myDirection, 7))


class ImageProcessingThread(QThread):
    processingFinished = pyqtSignal(list, bool)
    processingInterrupted = pyqtSignal()
    photoProcessed = pyqtSignal()

    def __init__(self, dir, photos, outputFileName, outputEncoding):
        QThread.__init__(self, QThread.currentThread())
        self.baseDir = dir
        self.photos = photos
        self.outputFileName = outputFileName
        self.outputEncoding = outputEncoding

        self.mutex = QMutex()
        self.stopMe = 0
        self.noTags = []

    def run(self):
        self.mutex.lock()
        self.stopMe = 0
        self.mutex.unlock()

        interrupted = False

        shapeFields = QgsFields()
        shapeFields.append(QgsField("filepath", QVariant.String, "", 255))
        shapeFields.append(QgsField("filename", QVariant.String, "", 255))
        shapeFields.append(QgsField("longitude", QVariant.Double))
        shapeFields.append(QgsField("latitude", QVariant.Double))
        shapeFields.append(QgsField("altitude", QVariant.Double))
        shapeFields.append(QgsField("north", QVariant.String, "", 1))
        shapeFields.append(QgsField("direction", QVariant.Double))
        shapeFields.append(QgsField("gps_date", QVariant.String, "", 255))
        shapeFields.append(QgsField("img_date", QVariant.String, "", 255))

        crs = QgsCoordinateReferenceSystem(4326)

        shapeFileWriter = QgsVectorFileWriter(self.outputFileName, self.outputEncoding, shapeFields, QGis.WKBPoint, crs)

        featureId = 0
        for fileName in self.photos:
            path = os.path.abspath(unicode(QFileInfo(self.baseDir + "/" + fileName).absoluteFilePath()))
            photoFile = open(path, "rb")
            exifTags = EXIF.process_file(photoFile, details=False)
            photoFile.close()

            # check for GPS tags. If no tags found, write message to log and skip this file
            if ("GPS GPSLongitude" not int exifTags) or ("GPS GPSLatitude" not in exifTags):
                self.noTags.append("%s - does not have GPS tags" % (path))
                self.photoProcessed.emit()
                continue

            (lon, lat) = getCoordinates(exifTags)
            # if coordinates are empty, write message to log and skip this file
            #if lon == 0 and lat == 0:
            #  self.noTags.append(QString("%1 - has null coordinates").arg(path))
            #  self.emit(SIGNAL("photoProcessed()"))
            #  continue

            altitude = getAltitude(exifTags)
            if altitude is None:
                altitude = 0

            imgDirection = getDirection(exifTags)
            if imgDirection is None:
                north = ""
                direction = 0
            else:
                north = imgDirection[0]
                direction = imgDirection[1]

            gpsDate = getGPSDateTime(exifTags)
            imgDate = getImageDateTime(exifTags)

            exifTags = None

            # write point to the shapefile
            feature = QgsFeature()
            feature.initAttributes(shapeFields.count())
            geometry = QgsGeometry()
            point = QgsPoint(lon, lat)
            feature.setGeometry(geometry.fromPoint(point))
            feature.setAttribute(0, path)
            feature.setAttribute(1, fileName)
            feature.setAttribute(2, lon)
            feature.setAttribute(3, lat)
            feature.setAttribute(4, altitude)
            feature.setAttribute(5, north)
            feature.setAttribute(6, direction)
            feature.setAttribute(7, gpsDate)
            feature.setAttribute(8, imgDate)
            shapeFileWriter.addFeature(feature)
            featureId += 1

            self.photoProcessed.emit()

            self.mutex.lock()
            s = self.stopMe
            self.mutex.unlock()
            if s == 1:
                interrupted = True
                break

        del shapeFileWriter
        haveShape = True

        if not interrupted:
            if featureId == 0:
                QgsVectorFileWriter.deleteShapeFile(self.outputFileName)
                haveShape = False
            self.processingFinished.emit(self.noTags, haveShape)
        else:
            self.processingInterrupted.emit()

    def stop(self):
        self.mutex.lock()
        self.stopMe = 1
        self.mutex.unlock()

        QThread.wait(self)
