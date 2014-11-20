# -*- coding: utf-8 -*-

"""
***************************************************************************
    photo2shapedialog.py
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from photo2shape.photoimporter import PhotoImporter

from photo2shape.ui.ui_photo2shapedialogbase import Ui_Dialog

import photo2shape.resources_rc


class Photo2ShapeDialog(QDialog, Ui_Dialog):
    def __init__(self, iface):
        QDialog.__init__(self)
        self.setupUi(self)

        self.iface = iface

        self.settings = QSettings('alexbruy', 'photo2shape')

        self.thread = QThread()
        self.importer = PhotoImporter()

        self.btnOk = self.buttonBox.button(QDialogButtonBox.Ok)
        self.btnClose = self.buttonBox.button(QDialogButtonBox.Close)

        self.btnSelectInput.clicked.connect(self.selectDirectory)
        self.btnSelectOutput.clicked.connect(self.selectFile)

        self.importer.moveToThread(self.thread)
        self.importer.importError.connect(self.thread.quit)
        self.importer.importError.connect(self.importCanceled)
        self.importer.importMessage.connect(self.logMessage)
        self.importer.importFinished.connect(self.thread.quit)
        self.importer.importFinished.connect(self.importCompleted)
        self.importer.photoProcessed.connect(self.updateProgress)

        self.manageGui()

    def manageGui(self):
        self.chkRecurse.setChecked(self.settings.value('recurse', True, bool))
        self.chkAppend.setChecked(self.settings.value('append', True, bool))
        self.chkLoadLayer.setChecked(
            self.settings.value('loadLayer', True, bool))

    def closeEvent(self, event):
        self.settings.setValue('recurse', self.chkRecurse.isChecked())
        self.settings.setValue('append', self.chkAppend.isChecked())
        self.settings.setValue('loadLayer', self.chkLoadLayer.isChecked())

        QDialog.closeEvent(self, event)

    def selectDirectory(self):
        lastDir = self.settings.value('lastPhotosDir', '.')
        dirName = QFileDialog.getExistingDirectory(
            self, self.tr('Select directory'), lastDir)

        if dirName == '':
            return

        self.lePhotosPath.setText(dirName)
        self.settings.setValue('lastPhotosDir', os.path.dirname(dirName))

    def selectFile(self):
        lastDir = self.settings.value('lastShapeDir', '.')
        shpFilter = self.tr('ESRI Shapefiles (*.shp *.SHP)')
        encoding = self.settings.value('encoding', 'System')

        fileDialog = QgsEncodingFileDialog(
            self, self.tr('Save file'), lastDir, shpFilter, encoding)

        fileDialog.setDefaultSuffix('shp')
        fileDialog.setFileMode(QFileDialog.AnyFile)
        fileDialog.setAcceptMode(QFileDialog.AcceptSave)
        fileDialog.setConfirmOverwrite(True)

        if fileDialog.exec_():
            fileName = fileDialog.selectedFiles()[0]
            self.encoding = fileDialog.encoding()

            self.leOutputShape.setText(fileName)
            self.settings.setValue('lastShapeDir',
                QFileInfo(fileName).absoluteDir().absolutePath())
            self.settings.setValue('encoding', encoding)

    def reject(self):
        QDialog.reject(self)

    def accept(self):
        dirName = self.lePhotosPath.text()
        if dirName == '':
            QMessageBox.warning(self,
                self.tr('Path not set'),
                self.tr('Path to photos is not set. Please specify directory '
                        'with photos and try again.'))
            return

        fileName = self.leOutputShape.text()
        if fileName == '':
            QMessageBox.warning(self,
                self.tr('Output file is not set'),
                self.tr('Output file name is missing. Please specify correct '
                        'output file and try again.'))
            return

        self.importer.setPhotosDirectory(dirName)
        self.importer.setOutputPath(fileName)
        self.importer.setEncoding(self.encoding)
        self.importer.setRecurseDirs(self.chkRecurse.isChecked())
        self.importer.setAppendFile(self.chkAppend.isChecked())

        self.thread.started.connect(self.importer.importPhotos)
        self.thread.start()
        self.btnOk.setEnabled(False)
        self.btnClose.setEnabled(False)

    def updateProgress(self, value):
        self.progressBar.setValue(value)

    def logMessage(self, message, level=QgsMessageLog.INFO):
        QgsMessageLog.logMessage(message, 'Photo2Shape', level)

    def importCanceled(self, message):
        self._showMessage(message, QgsMessageBar.WARNING)
        self._restoreGui()

    def importCompleted(self):
        self._showMessage(self.tr('Import completed'))
        if self.chkLoadLayer.isChecked():
            self._loadLayer()

        self._restoreGui()

    def _loadLayer(self):
        fName = self.leOutputShape.text()
        layer = QgsVectorLayer(fName, QFileInfo(fName).baseName(), 'ogr')

        if layer.isValid():
            layer.loadNamedStyle(':/resources/photos.qml')
            QgsMapLayerRegistry.instance().addMapLayer(layer)
        else:
            self.iface.messageBar().pushMessage(
                self.tr('Cannot load output shapefile'),
                QgsMessageBar.WARNING, self.iface.messageTimeout())

    def _restoreGui(self):
        self.thread.started.disconnect()
        self.progressBar.setValue(0)
        self.btnOk.setEnabled(True)
        self.btnClose.setEnabled(True)

    def _showMessage(self, message, level=QgsMessageBar.INFO):
        self.iface.messageBar().pushMessage(
            message, level, self.iface.messageTimeout())
