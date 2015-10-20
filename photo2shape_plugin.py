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

import os
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *

from photo2shape.gui.photo2shapedialog import Photo2ShapeDialog
from photo2shape.gui.aboutdialog import AboutDialog

import photo2shape.resources_rc


class Photo2ShapePlugin:
    def __init__(self, iface):
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        self.qgsVersion = unicode(QGis.QGIS_VERSION_INT)

        pluginPath = os.path.abspath(os.path.dirname(__file__))
        encoding = sys.getfilesystemencoding()
        pluginPath = pluginPath.decode(encoding)

        overrideLocale = QSettings().value('locale/overrideFlag', False, bool)
        if not overrideLocale:
            locale = QLocale.system().name()[:2]
        else:
            locale = QSettings().value('locale/userLocale', '')

        translationPath = pluginPath + '/i18n/photo2shape_' + locale + '.qm'

        if QFileInfo(translationPath).exists():
            self.translator = QTranslator()
            self.translator.load(translationPath)
            QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        if int(self.qgsVersion) < 20000:
            qgisVersion = self.qgsVersion[0] + '.' + self.qgsVersion[2] \
                + '.' + self.qgsVersion[3]
            QMessageBox.warning(self.iface.mainWindow(), 'Photo2Shape',
                QCoreApplication.translate('Photo2Shape',
                    'QGIS %s detected.\nThis version of Photo2Shape requires '
                    'at least QGIS 2.0.\nPlugin will not be enabled.') % (qgisVersion))
            return None

        self.actionRun = QAction(QCoreApplication.translate(
            'Photo2Shape', 'Photo2Shape'), self.iface.mainWindow())
        self.actionRun.setIcon(QIcon(':/icons/photo2shape.png'))
        self.actionRun.setWhatsThis(QCoreApplication.translate(
            'Photo2Shape', 'Create a point shapefile from geotagged images'))

        self.actionAbout = QAction(QCoreApplication.translate(
            'Photo2Shape', 'About Photo2Shape...'), self.iface.mainWindow())
        self.actionAbout.setIcon(QIcon(':/icons/about.png'))
        self.actionAbout.setWhatsThis(QCoreApplication.translate(
            'Photo2Shape', 'About Photo2Shape'))

        self.iface.addPluginToVectorMenu(QCoreApplication.translate(
            'Photo2Shape', 'Photo2Shape'), self.actionRun)
        self.iface.addPluginToVectorMenu(QCoreApplication.translate(
            'Photo2Shape', 'Photo2Shape'), self.actionAbout)
        self.iface.addVectorToolBarIcon(self.actionRun)

        self.actionRun.triggered.connect(self.run)
        self.actionAbout.triggered.connect(self.about)

    def unload(self):
        self.iface.removePluginVectorMenu(QCoreApplication.translate(
            'Photo2Shape', 'Photo2Shape'), self.actionRun)
        self.iface.removePluginVectorMenu(QCoreApplication.translate(
            'Photo2Shape', 'Photo2Shape'), self.actionAbout)
        self.iface.removeVectorToolBarIcon(self.actionRun)

    def run(self):
        dlg = Photo2ShapeDialog(self.iface)
        dlg.show()
        dlg.exec_()

    def about(self):
        d = AboutDialog()
        d.exec_()
