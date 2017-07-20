# -*- coding: utf-8 -*-

"""
***************************************************************************
    photo2shape_plugin.py
    ---------------------
    Date                 : February 2010
    Copyright            : (C) 2010-2017 by Alexander Bruy
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
__copyright__ = '(C) 2010-2017, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtCore import (QCoreApplication, QSettings, QLocale, QTranslator)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsApplication

from photo2shape.gui.photo2shapedialog import Photo2ShapeDialog
from photo2shape.gui.aboutdialog import AboutDialog

pluginPath = os.path.dirname(__file__)


class Photo2ShapePlugin:
    def __init__(self, iface):
        self.iface = iface

        overrideLocale = QSettings().value('locale/overrideFlag', False, bool)
        if not overrideLocale:
            locale = QLocale.system().name()[:2]
        else:
            locale = QSettings().value('locale/userLocale', '')

        qmPath = '{}/i18n/photo2shape_{}.qm'.format(pluginPath, locale)

        if os.path.exists(qmPath):
            self.translator = QTranslator()
            self.translator.load(qmPath)
            QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        self.actionRun = QAction(
            self.tr('Photo2Shape'), self.iface.mainWindow())
        self.actionRun.setIcon(
            QIcon(os.path.join(pluginPath, 'icons', 'photo2shape.png')))
        self.actionRun.setWhatsThis(
            self.tr('Create a point shapefile from geotagged images'))
        self.actionRun.setObjectName('runPhoto2Shape')

        self.actionAbout = QAction(
            self.tr('About Photo2Shape...'), self.iface.mainWindow())
        self.actionAbout.setIcon(
            QgsApplication.getThemeIcon('/mActionHelpContents.svg'))
        self.actionAbout.setWhatsThis(self.tr('About Photo2Shape'))
        self.actionRun.setObjectName('aboutPhoto2Shape')

        self.iface.addPluginToVectorMenu(
            self.tr('Photo2Shape'), self.actionRun)
        self.iface.addPluginToVectorMenu(
            self.tr('Photo2Shape'), self.actionAbout)
        self.iface.addVectorToolBarIcon(self.actionRun)

        self.actionRun.triggered.connect(self.run)
        self.actionAbout.triggered.connect(self.about)

    def unload(self):
        self.iface.removePluginVectorMenu(
            self.tr('Photo2Shape'), self.actionRun)
        self.iface.removePluginVectorMenu(
            self.tr('Photo2Shape'), self.actionAbout)
        self.iface.removeVectorToolBarIcon(self.actionRun)

    def run(self):
        dlg = Photo2ShapeDialog(self.iface)
        dlg.show()
        dlg.exec_()

    def about(self):
        d = AboutDialog()
        d.exec_()

    def tr(self, text):
        return QCoreApplication.translate('Photo2Shape', text)
