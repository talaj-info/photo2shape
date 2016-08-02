# -*- coding: utf-8 -*-

"""
***************************************************************************
    aboutdialog.py
    ---------------------
    Date                 : July 2013
    Copyright            : (C) 2013-2015 by Alexander Bruy
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
__date__ = 'July 2013'
__copyright__ = '(C) 2013-2015, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'


import os
import ConfigParser

from PyQt4 import uic
from PyQt4.QtCore import QUrl, QSettings, QLocale
from PyQt4.QtGui import (QDialogButtonBox, QTextDocument, QPixmap, QDialog,
    QDesktopServices)


pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'aboutdialogbase.ui'))


class AboutDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setupUi(self)

        self.btnHelp = self.buttonBox.button(QDialogButtonBox.Help)

        cfg = ConfigParser.SafeConfigParser()
        cfg.read(os.path.join(pluginPath, 'metadata.txt'))
        version = cfg.get('general', 'version')

        self.lblLogo.setPixmap(
            QPixmap(os.path.join(pluginPath, 'icons', 'photo2shape.png')))
        self.lblVersion.setText(self.tr('Version: {}'.format(version)))

        doc = QTextDocument()
        doc.setHtml(self.getAboutText())
        self.textBrowser.setDocument(doc)
        self.textBrowser.setOpenExternalLinks(True)

        self.buttonBox.helpRequested.connect(self.openHelp)

    def openHelp(self):
        overrideLocale = QSettings().value('locale/overrideFlag', False, bool)
        if not overrideLocale:
            locale = QLocale.system().name()[:2]
        else:
            locale = QSettings().value('locale/userLocale', '')

        if locale in ['uk']:
            QDesktopServices.openUrl(
                QUrl('http://hub.qgis.org/projects/photo2shape/wiki'))
        else:
            QDesktopServices.openUrl(
                QUrl('http://hub.qgis.org/projects/photo2shape/wiki'))

    def getAboutText(self):
        return self.tr(
            '<p>Create point shapefile from a set of geotagged photos. '
            'Inspired by ImagesToShape plugin from Tim Sutton.</p>'
            '<p>NOTE: plugin requires 3rd party Python package '
            'exifread >= 2.0.0</p>'
            '<p><strong>Developers</strong>: Alexander Bruy</p>'
            '<p><strong>Homepage</strong>: '
            '<a href="http://hub.qgis.org/projects/photo2shape">'
            'http://hub.qgis.org/projects/photo2shape</a></p>'
            '<p>Please report bugs at '
            '<a href="http://hub.qgis.org/projects/photo2shape/issues">'
            'bugtracker</a>.</p>')
