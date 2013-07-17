# -*- coding: utf-8 -*-

#******************************************************************************
#
# Photo2Shape
# ---------------------------------------------------------
# Create a point shapefile from a set of geotagged images.
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


import os
import ConfigParser

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

import photo2shapedialog

import resources_rc


class Photo2ShapePlugin(object):
    def __init__(self, iface):
        self.iface = iface

        self.qgsVersion = unicode(QGis.QGIS_VERSION_INT)

        # For i18n support
        userPluginPath = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/photo2shape"
        systemPluginPath = QgsApplication.prefixPath() + "/python/plugins/photo2shape"

        overrideLocale = QSettings().value("locale/overrideFlag", False)
        if not overrideLocale:
            localeFullName = QLocale.system().name()
        else:
            localeFullName = QSettings().value("locale/userLocale", "")

        if QFileInfo(userPluginPath).exists():
            translationPath = userPluginPath + "/i18n/photo2shape_" + localeFullName + ".qm"
        else:
            translationPath = systemPluginPath + "/i18n/photo2shape_" + localeFullName + ".qm"

        self.localePath = translationPath
        if QFileInfo(self.localePath).exists():
            self.translator = QTranslator()
            self.translator.load(self.localePath)
            QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        if int(self.qgsVersion) < 10900:
            qgisVersion = self.qgsVersion[0] + "." + self.qgsVersion[2] + "." + self.qgsVersion[3]
            QMessageBox.warning(self.iface.mainWindow(), "Photo2Shape",
                                QCoreApplication.translate("Photo2Shape", "Quantum GIS version detected: ") + qgisVersion +
                                QCoreApplication.translate("Photo2Shape", "This version of Photo2Shape requires at least QGIS version 2.0.\nPlugin will not be enabled.")
                               )
            return None

        self.actionRun = QAction(QIcon(":/photo2shape.png"), "Photo2Shape", self.iface.mainWindow())
        self.actionRun.setStatusTip(QCoreApplication.translate("Photo2Shape", "Create a point shapefile from a set of geotagged images"))
        self.actionRun.setWhatsThis(QCoreApplication.translate("Photo2Shape", "Create a point shapefile from a set of geotagged images"))
        self.actionAbout = QAction(QIcon(":/about.png"), "About", self.iface.mainWindow())

        self.actionRun.triggered.connect(self.run)
        self.actionAbout.triggered.connect(self.about)

        self.iface.addPluginToVectorMenu(QCoreApplication.translate("Photo2Shape", "Photo2Shape"), self.actionRun)
        self.iface.addPluginToVectorMenu(QCoreApplication.translate("Photo2Shape", "Photo2Shape"), self.actionAbout)
        self.iface.addVectorToolBarIcon(self.actionRun)

    def unload(self):
        self.iface.removePluginVectorMenu(QCoreApplication.translate("Photo2Shape", "Photo2Shape"), self.actionRun)
        self.iface.removePluginVectorMenu(QCoreApplication.translate("Photo2Shape", "Photo2Shape"), self.actionAbout)
        self.iface.removeVectorToolBarIcon(self.actionRun)

    def about(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read(os.path.join(os.path.dirname(__file__), "metadata.txt"))
        version = cfg.get("general", "version")

        dlgAbout = QDialog()
        dlgAbout.setWindowTitle(QApplication.translate("Photo2Shape", "About Photo2Shape", "Window title"))
        lines = QVBoxLayout(dlgAbout)
        title = QLabel(QApplication.translate("Photo2Shape", "<b>Photo2Shape</b>"))
        title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        lines.addWidget(title)
        version = QLabel(QApplication.translate("Photo2Shape", "Version: %s") % (version))
        version.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        lines.addWidget(version)
        lines.addWidget(QLabel(QApplication.translate("Photo2Shape", "This plugin creates a point shapefile\nfrom a set of geotagged images")))
        lines.addWidget(QLabel(QApplication.translate("Photo2Shape", "<b>Developers:</b>")))
        lines.addWidget(QLabel("  Tim Sutton"))
        lines.addWidget(QLabel("  Alexander Bruy"))
        lines.addWidget(QLabel(QApplication.translate("Photo2Shape", "<b>Homepage:</b>")))

        overrideLocale = QSettings().value("locale/overrideFlag", False)
        if not overrideLocale:
            localeFullName = QLocale.system().name()
        else:
            localeFullName = QSettings().value("locale/userLocale", "")

        localeShortName = localeFullName[0:2]
        if localeShortName in ["ru", "uk"]:
            link = QLabel("<a href=\"http://hub.qgis.org/projects/photo2shape\">http://hub.qgis.org/projects/photo2shape</a>")
        else:
            link = QLabel("<a href=\"http://hub.qgis.org/projects/photo2shape\">http://hub.qgis.org/projects/photo2shape</a>")

        link.setOpenExternalLinks(True)
        lines.addWidget(link)

        btnClose = QPushButton(QApplication.translate("Photo2Shape", "Close"))
        lines.addWidget(btnClose)
        btnClose.clicked.connect(dlgAbout.close)

        dlgAbout.exec_()

    def run(self):
        dlg = photo2shapedialog.Photo2ShapeDialog()
        dlg.exec_()
