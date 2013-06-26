# -*- coding: utf-8 -*-

#******************************************************************************
#
# Photo2Shape
# ---------------------------------------------------------
# Create a point shapefile from a set of geotagged images
#
# Heavily based on ImagesToShape plugin (C) 2009 by Tim Sutton
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

def lastShapefileDir():
  settings = QSettings()
  lastProjectDir = settings.value("/UI/lastProjectDir", ".")
  return settings.value("/photo2shape/lastShapeDir", lastProjectDir)

def setLastShapefileDir(path):
  settings = QSettings()
  fileInfo = QFileInfo(path)
  if fileInfo.isDir():
    lastDir = fileInfo.filePath()
  else:
    lastDir = fileInfo.path()
  settings.setValue("/photo2shape/lastShapeDir", lastDir)

def lastPhotosDir():
  settings = QSettings()
  lastProjectDir = settings.value("/UI/lastProjectDir", ".")
  return settings.value("/photo2shape/lastPhotosDir", lastProjectDir)

def setLastPhotosDir(path):
  settings = QSettings()
  fileInfo = QFileInfo(path)
  if fileInfo.isDir():
    lastDir = fileInfo.filePath()
  else:
    lastDir = fileInfo.path()
  settings.setValue("/photo2shape/lastPhotosDir", lastDir)

def addToCanvas():
  settings = QSettings()
  return bool(settings.value("/photo2shape/addToCanvas", True))

def setAddToCanvas(state):
  settings = QSettings()
  settings.setValue("/photo2shape/addToCanvas", state)
