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

from photo2shapedialogbase import Ui_Photo2ShapeDialog

class Photo2ShapeDialog( QDialog, Ui_Photo2ShapeDialog ):
  def __init__( self ):
    QDialog.__init__( self )
    self.setupUi( self )

    self.photoProcessingThread = None

    self.okButton = self.buttonBox.button( QDialogButtonBox.Ok )
    self.closeButton = self.buttonBox.button( QDialogButtonBox.Close )

    QObject.connect( self.selectInputDirButton, SIGNAL( "clicked()" ), self.selectInputDir )
    QObject.connect( self.selectOutputFileButton, SIGNAL( "clicked()" ), self.selectOutputFile )

  def selectInputDir( self ):
    inputDir = QFileDialog.getExistingDirectory( self, self.tr( "Select directory with images" ) )
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
    
    self.progressBar.setRange( 0, self.inputFiles.count() )
    self.inputDirEdit.setText( inputDir )

  def selectOutputFile( self ):
    # prepare dialog parameters
    settings = QSettings()
    lastDir = settings.value( "/UI/lastShapefileDir" ).toString()
    filter = QString( "Shapefiles (*.shp *.SHP)" )

    fileDialog = QgsEncodingFileDialog( self, self.tr( "Select output shapefile" ), lastDir, filter, QString() )
    fileDialog.setDefaultSuffix( QString( "shp" ) )
    fileDialog.setFileMode( QFileDialog.AnyFile )
    fileDialog.setAcceptMode( QFileDialog.AcceptSave )
    fileDialog.setConfirmOverwrite( True )

    if not fileDialog.exec_() == QDialog.Accepted:
      return

    outputFile = fileDialog.selectedFiles()
    self.outputEncoding = fileDialog.encoding()

    self.outputFileEdit.setText( outputFile.first() )

  def accept( self ):
    outFileName = self.outputFileEdit.text()
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
    QObject.connect( self.photoProcessingThread, SIGNAL( "processingFinished( PyQt_PyObject )" ), self.processingFinished )
    QObject.connect( self.photoProcessingThread, SIGNAL( "processingInterrupted()" ), self.processingInterrupted )

    self.closeButton.setText( self.tr( "Cancel" ) )
    QObject.disconnect( self.buttonBox, SIGNAL( "rejected()" ), self.reject )
    QObject.connect( self.closeButton, SIGNAL( "clicked()" ), self.stopProcessing )

    self.photoProcessingThread.start()

  def photoProcessed( self ):
    self.progressBar.setValue( self.progressBar.value() + 1 )

  def processingFinished( self, errorsList ):
    self.stopProcessing()

    if not errorsList.isEmpty():
      msg = QString( "The following files does added to shapefile because of errors: <br><br>" ).append( errorsList.join( "<br><br>" ) )
      dlgError = QErrorMessage( self )
      dlgError.showMessage( msg )

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

def getCoordinates( tags ):
  exifTags = tags

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
  pass

def getDateTime( tags ):
  pass

def getDirection( tags ):
  pass

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

    shapeFields = { 0:QgsField( "filepath", QVariant.String ),
                    1:QgsField( "filename", QVariant.String ),
                    2:QgsField( "longitude", QVariant.Double ),
                    3:QgsField( "latitude", QVariant.Double ),
                    4:QgsField( "altitude", QVariant.Double ) }
    shapeFileWriter = QgsVectorFileWriter( self.outputFileName, self.outputEncoding, shapeFields, QGis.WKBPoint, None )

    featureId = 0
    for fileName in self.photos:
      path = QFileInfo( self.baseDir + "/" + fileName ).absoluteFilePath()
      photoFile = open( path, "rb" )
      exifTags = EXIF.process_file( photoFile )
      photoFile.close()

      # check for GPS tags. If no tags found, write message to log and skip this file
      if ( not exifTags.has_key( "GPS GPSLongitudeRef" ) ) or ( not exifTags.has_key( "GPS GPSLatitudeRef" ) ):
        self.noTags.append( QString( "%1 - does not have GPS tags" ).arg( path ) )
        self.emit( SIGNAL( "photoProcessed()" ) )
        continue

      ( lon, lat ) = getCoordinates( exifTags )

      # if coordinates are empty, write message to log and skip this file
      #if lon == 0 and lat == 0:
      #  self.noTags.append( QString( "%1 - has null coordinates" ).arg( path ) )
      #  self.emit( SIGNAL( "photoProcessed()" ) )
      #  continue

      # write point to the shapefile
      feature = QgsFeature()
      geometry = QgsGeometry()
      point = QgsPoint( lon, lat )
      feature.setGeometry( geometry.fromPoint( point ) )
      feature.addAttribute( 0, path )
      feature.addAttribute( 1, fileName )
      feature.addAttribute( 2, QVariant( lon ) )
      feature.addAttribute( 3, QVariant( lat ) )
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

    if not interrupted:
      self.emit( SIGNAL( "processingFinished( PyQt_PyObject )" ), self.noTags )
    else:
      self.emit( SIGNAL( "processingInterrupted()" ) )

  def stop( self ):
    self.mutex.lock()
    self.stopMe = 1
    self.mutex.unlock()

    QThread.wait( self )

