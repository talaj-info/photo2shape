# -*- coding: utf-8 -*-

#******************************************************************************
#
# Photo2Shape
# ---------------------------------------------------------
# Create a point shapefile from a set of geotagged images
#
# Heavily based on ImagesToShape plugin (C) 2009 by Tim Sutton
#
# Copyright (C) 2010 Alexander Bruy (alexander.bruy@gmail.com)
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

import os.path, re
import EXIF

import photo2shape_utils as utils

from ui_photo2shapedialogbase import Ui_Photo2ShapeDialog

class Photo2ShapeDialog( QDialog, Ui_Photo2ShapeDialog ):
  def __init__( self ):
    QDialog.__init__( self )
    self.setupUi( self )

    self.photoProcessingThread = None

    self.okButton = self.buttonBox.button( QDialogButtonBox.Ok )
    self.closeButton = self.buttonBox.button( QDialogButtonBox.Close )

    QObject.connect( self.selectInputDirButton, SIGNAL( "clicked()" ), self.selectInputDir )
    QObject.connect( self.selectOutputFileButton, SIGNAL( "clicked()" ), self.selectOutputFile )

    self.manageGui()

  def manageGui( self ):
    self.addToCanvasCheck.setCheckState( utils.addToCanvas() )

  def selectInputDir( self ):
    inputDir = QFileDialog.getExistingDirectory( self,
                           self.tr( "Select directory with images" ),
                           utils.lastPhotosDir() )
    if inputDir.isEmpty():
      return

    workDir = QDir( inputDir )
    workDir.setFilter( QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot )
    nameFilter = QStringList() << "*.jpg" << "*.jpeg" << "*.JPG" << "*.JPEG"
    workDir.setNameFilters( nameFilter )
    self.inputFiles = workDir.entryList()
    if self.inputFiles.count() == 0:
      QMessageBox.warning( self, self.tr( "No images found" ), self.tr( "There are no supported images in this directory. Please select another one." ) )
      self.inputFiles = None
      return

    utils.setLastPhotosDir( inputDir )
    self.progressBar.setRange( 0, self.inputFiles.count() )
    self.inputDirEdit.setText( inputDir )

  def selectOutputFile( self ):
    # prepare dialog parameters
    settings = QSettings()
    lastDir = utils.lastShapefileDir()
    shpFilter = QString( "Shapefiles (*.shp *.SHP)" )

    fileDialog = QgsEncodingFileDialog( self, self.tr( "Select output shapefile" ), lastDir, shpFilter, QString() )
    fileDialog.setDefaultSuffix( QString( "shp" ) )
    fileDialog.setFileMode( QFileDialog.AnyFile )
    fileDialog.setAcceptMode( QFileDialog.AcceptSave )
    fileDialog.setConfirmOverwrite( True )

    if not fileDialog.exec_() == QDialog.Accepted:
      return

    outputFile = fileDialog.selectedFiles()
    self.outputEncoding = fileDialog.encoding()

    utils.setLastShapefileDir( outputFile.first() )
    self.outputFileEdit.setText( outputFile.first() )

  def reject( self ):
    utils.setAddToCanvas( self.addToCanvasCheck.checkState() )

    QDialog.reject( self )

  def accept( self ):
    outFileName = self.outputFileEdit.text()

    if outFileName.isEmpty():
      QMessageBox.warning( self, self.tr( "Wrong output file" ),
         self.tr( "Output file is improperly defined.\nPlease enter a valid filename and try again." ) )
      return


    outFile = QFile( outFileName )
    if outFile.exists():
      if not QgsVectorFileWriter.deleteShapeFile( outFileName ):
        QMessageBox.warning( self, self.tr( "Delete error" ), self.tr( "Can't delete file %1" ).arg( outFileName ) )
        return

    baseDir = self.inputDirEdit.text()

    QApplication.setOverrideCursor( QCursor( Qt.WaitCursor ) )
    self.okButton.setEnabled( False )

    self.photoProcessingThread = ImageProcessingThread( baseDir, self.inputFiles, outFileName, self.outputEncoding )
    QObject.connect( self.photoProcessingThread, SIGNAL( "photoProcessed()" ), self.photoProcessed )
    QObject.connect( self.photoProcessingThread, SIGNAL( "processingFinished( PyQt_PyObject, PyQt_PyObject )" ), self.processingFinished )
    QObject.connect( self.photoProcessingThread, SIGNAL( "processingInterrupted()" ), self.processingInterrupted )

    self.closeButton.setText( self.tr( "Cancel" ) )
    QObject.disconnect( self.buttonBox, SIGNAL( "rejected()" ), self.reject )
    QObject.connect( self.closeButton, SIGNAL( "clicked()" ), self.stopProcessing )

    self.photoProcessingThread.start()

  def photoProcessed( self ):
    self.progressBar.setValue( self.progressBar.value() + 1 )

  def processingFinished( self, errorsList, hasOutput ):
    self.stopProcessing()

    if not hasOutput:
      QMessageBox.warning( self, self.tr( "Photo2Shape" ),
                  self.tr( "There are no geotagged photos in selected directory.\nShapefile was not created." ) )
      self.restoreGUI()
      return

    if not errorsList.isEmpty():
      msg = QString( "The following files were not added to shapefile because of errors: <br><br>" ).append( errorsList.join( "<br><br>" ) )
      dlgError = QErrorMessage( self )
      dlgError.showMessage( msg )

    self.writeQml()
    if self.addToCanvasCheck.isChecked():
      self.addLayerToCanvas()

    self.restoreGUI()

  def processingInterrupted( self ):
    self.restoreGUI()

  def stopProcessing( self ):
    if self.photoProcessingThread != None:
      self.photoProcessingThread.stop()
      self.photoProcessingThread = None

  def restoreGUI( self ):
    self.progressBar.setValue( 0 )
    QApplication.restoreOverrideCursor()
    QObject.connect( self.buttonBox, SIGNAL( "rejected()" ), self.reject )
    self.closeButton.setText( self.tr( "Close" ) )
    self.okButton.setEnabled( True )

  def addLayerToCanvas( self ):
    layerPath = self.outputFileEdit.text()
    newLayer = QgsVectorLayer( layerPath, QFileInfo( layerPath ).baseName(), "ogr" )

    if newLayer.isValid():
      QgsMapLayerRegistry.instance().addMapLayer( newLayer )
    else:
      QMessageBox.warning( self, self.tr( "Photo2Shape" ),
                           self.tr( "Error loading output shapefile:\n%1" )
                           .arg( unicode( layerPath ) ) )

  def writeQml( self ):
    if not QFile( self.outputFileEdit.text() ).exists():
      return

    sourceQml = os.path.join( os.path.dirname( __file__ ), "photos.qml" )
    sourceFile = QFile( sourceQml )
    outputQml = self.outputFileEdit.text().replace( QRegExp( "\.shp$" ), ".qml" )
    outputFile = QFile( outputQml )
    if outputFile.exists():
      res = QMessageBox.question( self, self.tr( "QML exists" ),
                        self.tr( "QML file %1 already exists. Overwrite?" )
                        .arg( outputQml ),
                        QMessageBox.Yes | QMessageBox.No )
      if res != QMessageBox.Yes:
        return
      outputFile.remove()

    if not sourceFile.copy( outputQml ):
      QMessageBox.warning( self, self.tr( "QML error" ), self.tr( "Can't write QML file" ) )

def getCoordinates( tags ):
  exifTags = tags

  # some devices (e.g. with Android 1.6 ) write tags in non standard way
  # as decimal degrees in ASCII field
  if EXIF.FIELD_TYPES[ exifTags[ "GPS GPSLongitude" ].field_type ][ 2 ] == 'ASCII':
    strLon = str( exifTags[ "GPS GPSLongitude" ] )
    strLat = str( exifTags[ "GPS GPSLatitude" ] )
    lon = round( float( strLon ), 7 )
    lat = round( float( strLat ), 7 )
    return ( lon, lat )

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
  lonDirection = str( exifTags[ "GPS GPSLongitudeRef" ] )
  # EXIF returns degrees, minutes and seconds in list, so we need to split it
  longitude = str( exifTags[ "GPS GPSLongitude" ] )[ 1:-1 ].split( ", " )
  lonDegrees = longitude[ 0 ]
  lonMinutes = longitude[ 1 ]
  lonSeconds = longitude[ 2 ]

  # latitude direction will be either "N" or "S"
  latDirection = str( exifTags[ "GPS GPSLatitudeRef" ] )
  # EXIF returns degrees, minutes and seconds in list, so we need to split it
  latitude = str( exifTags[ "GPS GPSLatitude" ] )[ 1:-1 ].split( ", " )
  latDegrees = latitude[ 0 ]
  latMinutes = latitude[ 1 ]
  latSeconds = latitude[ 2 ]

  # get the degree, minutes and seconds values
  regexp = re.compile( "^[0-9]*" )
  lonDegreesFloat = float( regexp.search( str( lonDegrees ) ).group() )
  lonMinutesFloat = float( regexp.search( str( lonMinutes ) ).group() )
  lonSecondsFloat = float( regexp.search( str( lonSeconds ) ).group() )
  latDegreesFloat = float( regexp.search( str( latDegrees ) ).group() )
  latMinutesFloat = float( regexp.search( str( latMinutes ) ).group() )
  latSecondsFloat = float( regexp.search( str( latSeconds ) ).group() )

  # divide the values by the divisor if neccessary
  regexp = re.compile( "[0-9]*$" )
  if lonDegrees.find( "/" ) == -1:
    myLonDegrees = lonDegreesFloat
  else:
    myLonDegrees = lonDegreesFloat / float( regexp.search( str( lonDegrees ) ).group() )
  if lonMinutes.find( "/" ) == -1:
    myLonMinutes = lonMinutesFloat
  else:
    myLonMinutes = lonMinutesFloat / float( regexp.search( str( lonMinutes ) ).group() )
  if lonSeconds.find( "/" ) == -1:
    myLonSeconds = lonSecondsFloat
  else:
    myLonSeconds = lonSecondsFloat / float( regexp.search( str( lonSeconds ) ).group() )

  if latDegrees.find( "/" ) == -1:
    myLatDegrees = latDegreesFloat
  else:
    myLatDegrees = latDegreesFloat / float( regexp.search( str( latDegrees ) ).group() )
  if latMinutes.find( "/" ) == -1:
    myLatMinutes = latMinutesFloat
  else:
    myLatMinutes = latMinutesFloat / float( regexp.search( str( latMinutes ) ).group() )
  if latSeconds.find( "/" ) == -1:
    myLatSeconds = latSecondsFloat
  else:
    myLatSeconds = latSecondsFloat / float( regexp.search( str( latSeconds ) ).group() )

  # we now have degrees, decimal minutes and decimal seconds, so convert to decimal degrees
  lon = round( myLonDegrees + ( myLonMinutes / 60 ) + ( myLonSeconds / 3600 ), 7 )
  lat = round( myLatDegrees + ( myLatMinutes / 60 ) + ( myLatSeconds / 3600 ), 7 )

  # use a negative sign as needed
  if lonDirection == "W":
    lon = 0 - lon
  if latDirection == "S":
    lat = 0 - lat

  return ( lon, lat )

def getAltitude( tags ):
  exifTags = tags

  if not exifTags.has_key( "GPS GPSAltitude" ):
    return None

  # some devices (e.g. with Android 1.6 ) write tags in non standard way
  # as decimal degrees in ASCII field also they don't write
  # GPS GPSAltitudeRef tag
  if EXIF.FIELD_TYPES[ exifTags[ "GPS GPSAltitude" ].field_type ][ 2 ] == 'ASCII':
    alt = str( exifTags[ "GPS GPSAltitude" ] )
    return round( float( alt ), 7 )

  if not exifTags.has_key( "GPS GPSAltitudeRef" ):
    return None

  # altitude
  altDirection = exifTags[ "GPS GPSAltitudeRef" ]
  altitude = str( exifTags[ "GPS GPSAltitude" ] )

  # get altitude value
  regexp = re.compile( "^[0-9]*" )
  altitudeFloat = float( regexp.search( str( altitude ) ).group() )

  # divide the value by the divisor if neccessary
  regexp = re.compile( "[0-9]*$" )
  if altitude.find( "/" ) == -1:
    myAltitude = altitudeFloat
  else:
    myAltitude = altitudeFloat / float( regexp.search( str( altitude ) ).group() )

  # use negative sign as needed
  if altDirection == 1:
    myAltitude = 0 - myAltitude

  return round( myAltitude, 7 )

def getGPSDateTime( tags ):
  exifTags = tags

  imgDate = None
  imgTime = None

  if exifTags.has_key( "GPS GPSDate" ):
    imgDate = str( exifTags[ "GPS GPSDate" ] )

  if exifTags.has_key( "GPS GPSTimeStamp" ):
    # some devices (e.g. Android) save this tag in non-standard way
    if EXIF.FIELD_TYPES[ exifTags[ "GPS GPSTimeStamp" ].field_type ][ 2 ] == 'ASCII':
      return str( exifTags[ "GPS GPSTimeStamp" ] )
    else:
      tmp = str( exifTags[ "GPS GPSTimeStamp" ] )[ 1:-1 ].split( ", " )
      imgTime = tmp[ 0 ] + ":" + tmp[ 1 ] + ":" + tmp[ 2 ]
      if imgDate is None:
        return imgTime
      return imgDate + " " + imgTime

  return None

def getImageDateTime( tags ):
  exifTags = tags

  if exifTags.has_key( "Image DateTime" ):
    return str( exifTags[ "Image DateTime" ] )

  return None

def getDirection( tags ):
  exifTags = tags

  if not exifTags.has_key( "GPS GPSImgDirection" ):
    return None

  myAzimuth = str( exifTags[ "GPS GPSImgDirectionRef" ] )
  direction = str( exifTags[ "GPS GPSImgDirection" ] )

  # get direction value
  regexp = re.compile( "^[0-9]*" )
  directionFloat = float( regexp.search( str( direction ) ).group() )

  # divide the value by the divisor if neccessary
  regexp = re.compile( "[0-9]*$" )
  if direction.find( "/" ) == -1:
    myDirection = directionFloat
  else:
    myDirection = directionFloat / float( regexp.search( str( direction ) ).group() )

  return ( myAzimuth, round( myDirection, 7 ) )

class ImageProcessingThread( QThread ):
  def __init__( self, dir, photos, outputFileName, outputEncoding ):
    QThread.__init__( self, QThread.currentThread() )
    self.baseDir = dir
    self.photos = photos
    self.outputFileName = outputFileName
    self.outputEncoding = outputEncoding

    self.mutex = QMutex()
    self.stopMe = 0
    self.noTags = QStringList()

  def run( self ):
    self.mutex.lock()
    self.stopMe = 0
    self.mutex.unlock()

    interrupted = False

    shapeFields = { 0:QgsField( "filepath", QVariant.String, QString(), 255 ),
                    1:QgsField( "filename", QVariant.String, QString(), 255 ),
                    2:QgsField( "longitude", QVariant.Double ),
                    3:QgsField( "latitude", QVariant.Double ),
                    4:QgsField( "altitude", QVariant.Double ),
                    5:QgsField( "north", QVariant.String, QString(), 1 ),
                    6:QgsField( "direction", QVariant.Double ),
                    7:QgsField( "gps_date", QVariant.String, QString(), 255 ),
                    8:QgsField( "img_date", QVariant.String, QString(), 255 ) }

    crs = QgsCoordinateReferenceSystem( 4326 )

    shapeFileWriter = QgsVectorFileWriter( self.outputFileName, self.outputEncoding, shapeFields, QGis.WKBPoint, crs )

    featureId = 0
    for fileName in self.photos:
      path = os.path.abspath( unicode( QFileInfo( self.baseDir + "/" + fileName ).absoluteFilePath() ) )
      photoFile = open( path, "rb" )
      exifTags = EXIF.process_file( photoFile, details=False )
      photoFile.close()

      # check for GPS tags. If no tags found, write message to log and skip this file
      if ( not exifTags.has_key( "GPS GPSLongitude" ) ) or ( not exifTags.has_key( "GPS GPSLatitude" ) ):
        self.noTags.append( QString( "%1 - does not have GPS tags" ).arg( path ) )
        self.emit( SIGNAL( "photoProcessed()" ) )
        continue

      ( lon, lat ) = getCoordinates( exifTags )
      # if coordinates are empty, write message to log and skip this file
      #if lon == 0 and lat == 0:
      #  self.noTags.append( QString( "%1 - has null coordinates" ).arg( path ) )
      #  self.emit( SIGNAL( "photoProcessed()" ) )
      #  continue

      altitude = getAltitude( exifTags )
      if altitude == None:
        altitude = 0

      imgDirection = getDirection( exifTags )
      if imgDirection == None:
        north = ""
        direction = 0
      else:
        north = imgDirection[ 0 ]
        direction = imgDirection[ 1 ]

      gpsDate = getGPSDateTime( exifTags )
      imgDate = getImageDateTime( exifTags )

      exifTags = None

      # write point to the shapefile
      feature = QgsFeature()
      geometry = QgsGeometry()
      point = QgsPoint( lon, lat )
      feature.setGeometry( geometry.fromPoint( point ) )
      feature.addAttribute( 0, path )
      feature.addAttribute( 1, fileName )
      feature.addAttribute( 2, QVariant( lon ) )
      feature.addAttribute( 3, QVariant( lat ) )
      feature.addAttribute( 4, QVariant( altitude ) )
      feature.addAttribute( 5, QVariant( north ) )
      feature.addAttribute( 6, QVariant( direction ) )
      feature.addAttribute( 7, QVariant( gpsDate ) )
      feature.addAttribute( 8, QVariant( imgDate ) )
      shapeFileWriter.addFeature( feature )
      featureId += 1

      self.emit( SIGNAL( "photoProcessed()" ) )

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
        QgsVectorFileWriter.deleteShapeFile( self.outputFileName )
        haveShape = False
      self.emit( SIGNAL( "processingFinished( PyQt_PyObject, PyQt_PyObject )" ), self.noTags, haveShape )
    else:
      self.emit( SIGNAL( "processingInterrupted()" ) )

  def stop( self ):
    self.mutex.lock()
    self.stopMe = 1
    self.mutex.unlock()

    QThread.wait( self )

