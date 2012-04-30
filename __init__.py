# -*- coding: utf-8 -*-

mVersion = "0.1.23"

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

def name():
  return "Photo2Shape"

def description():
  return "Create a point shapefile from a set of geotagged images"

def category():
  return "Vector"

def version():
  return mVersion

def qgisMinimumVersion():
  return "1.0"

def authorName():
  return "Alexander Bruy"

def icon():
  return "photo2shape.png"

def classFactory( iface ):
  from photo2shape import Photo2ShapePlugin
  return Photo2ShapePlugin( iface )

