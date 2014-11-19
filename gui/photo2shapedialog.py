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
        self.importer.importFinished.connect(self.thread.quit)
        self.importer.importFinished.connect(self.importCompleted)
        self.importer.photoProcessed.connect(self.updateProgress)

        self.manageGui()

    def manageGui(self):
        self.chkAddToCanvas.setChecked(
            self.settings.value('addToCanvas', True, bool))

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

        #~ outFile = QFile(outFileName)
        #~ if outFile.exists():
            #~ if not QgsVectorFileWriter.deleteShapeFile(outFileName):
                #~ QMessageBox.warning(
                    #~ self, self.tr("Delete error"),
                    #~ self.tr("Can't delete file %s") % outFileName)
                #~ return

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

    def importCompleted(self):
        self.thread.started.disconnect()
        self.iface.messageBar().pushMessage(self.tr('Import completed'),
            QgsMessageBar.INFO, self.iface.messageTimeout())
        self.progressBar.setValue(0)
        self.btnOk.setEnabled(True)
        self.btnClose.setEnabled(True)

    #~ def processingFinished(self, errorsList, hasOutput):
        #~ self.stopProcessing()
#~
        #~ if not hasOutput:
            #~ QMessageBox.warning(self,
                                #~ self.tr("Photo2Shape"),
                                #~ self.tr("There are no geotagged photos in selected directory.\nShapefile was not created.")
                               #~ )
            #~ self.restoreGUI()
            #~ return
#~
        #~ if len(errorsList) > 0:
            #~ msg = self.tr("The following files were not added to shapefile because of errors: <br><br>") + "<br><br>".join(errorsList)
            #~ dlgError = QErrorMessage(self)
            #~ dlgError.showMessage(msg)
#~
        #~ self.writeQml()
        #~ if self.addToCanvasCheck.isChecked():
            #~ self.addLayerToCanvas()
#~
        #~ self.restoreGUI()
#~
    #~ def processingInterrupted(self):
        #~ self.restoreGUI()
#~
    #~ def stopProcessing(self):
        #~ if self.workThread is not None:
            #~ self.workThread.stop()
            #~ self.workThread = None
#~
    #~ def restoreGUI(self):
        #~ self.progressBar.setValue(0)
        #~ self.buttonBox.rejected.connect(self.reject)
        #~ self.btnClose.setText(self.tr("Close"))
        #~ self.btnOk.setEnabled(True)
#~
    #~ def addLayerToCanvas(self):
        #~ layerPath = self.outputFileEdit.text()
        #~ newLayer = QgsVectorLayer(layerPath, QFileInfo(layerPath).baseName(), "ogr")
#~
        #~ if newLayer.isValid():
            #~ QgsMapLayerRegistry.instance().addMapLayer(newLayer)
        #~ else:
            #~ QMessageBox.warning(self,
                                #~ self.tr("Photo2Shape"),
                                #~ self.tr("Error loading output shapefile:\n%s") % (layerPath)
                               #~ )
#~
    #~ def writeQml(self):
        #~ outputQml = self.outputFileEdit.text().replace(".shp", ".qml")
        #~ outputFile = QFile(outputQml)
        #~ if outputFile.exists():
            #~ res = QMessageBox.question(self,
                                       #~ self.tr("QML exists"),
                                       #~ self.tr("QML file %s already exists. Overwrite?") % (outputQml),
                                       #~ QMessageBox.Yes | QMessageBox.No
                                      #~ )
            #~ if res != QMessageBox.Yes:
                #~ return
            #~ outputFile.remove()
#~
        #~ templateFile = QFile(":/resources/photos.qml")
        #~ if templateFile.open(QIODevice.ReadOnly):
            #~ if outputFile.open(QIODevice.WriteOnly):
                #~ outputFile.write(templateFile.readAll())
            #~ outputFile.close()
        #~ templateFile.close()
