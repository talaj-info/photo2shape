# -*- coding: utf-8 -*-

"""
***************************************************************************
    photo2shape_plugin.py
    ---------------------
    Date                 : February 2010
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
__date__ = 'February 2010'
__copyright__ = '(C) 2010-2014, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'


from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from photo2shape.gui.photo2shapedialog import Photo2ShapeDialog
from photo2shape.gui.aboutdialog import AboutDialog

import photo2shape.resources_rc


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
                                QCoreApplication.translate("Photo2Shape", "QGIS version detected: ") + qgisVersion +
                                QCoreApplication.translate("Photo2Shape", "This version of Photo2Shape requires at least QGIS version 2.0.\nPlugin will not be enabled.")
                               )
            return None

        self.actionRun = QAction(QIcon(":/icons/photo2shape.png"), "Photo2Shape", self.iface.mainWindow())
        self.actionRun.setStatusTip(QCoreApplication.translate("Photo2Shape", "Create a point shapefile from a set of geotagged images"))
        self.actionRun.setWhatsThis(QCoreApplication.translate("Photo2Shape", "Create a point shapefile from a set of geotagged images"))
        self.actionAbout = QAction(QIcon(":/icons/about.png"), "About", self.iface.mainWindow())

        self.actionRun.triggered.connect(self.run)
        self.actionAbout.triggered.connect(self.about)

        self.iface.addPluginToVectorMenu(QCoreApplication.translate("Photo2Shape", "Photo2Shape"), self.actionRun)
        self.iface.addPluginToVectorMenu(QCoreApplication.translate("Photo2Shape", "Photo2Shape"), self.actionAbout)
        self.iface.addVectorToolBarIcon(self.actionRun)

    def unload(self):
        self.iface.removePluginVectorMenu(QCoreApplication.translate("Photo2Shape", "Photo2Shape"), self.actionRun)
        self.iface.removePluginVectorMenu(QCoreApplication.translate("Photo2Shape", "Photo2Shape"), self.actionAbout)
        self.iface.removeVectorToolBarIcon(self.actionRun)

    def run(self):
        dlg = Photo2ShapeDialog()
        dlg.exec_()

    def about(self):
        d = AboutDialog()
        d.exec_()
