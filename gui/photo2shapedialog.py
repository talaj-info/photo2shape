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
__date__ = 'February 2014'
__copyright__ = '(C) 2010-2014, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'


from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

import os.path
import re

from photo2shape.importthread import ImportThread

from photo2shape.ui.ui_photo2shapedialogbase import Ui_Photo2ShapeDialog

import photo2shape.resources_rc


class Photo2ShapeDialog(QDialog, Ui_Photo2ShapeDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)

        self.settings = QSettings("alexbruy", "photo2shape")
        self.workThread = None

        self.btnOk = self.buttonBox.button(QDialogButtonBox.Ok)
        self.btnClose = self.buttonBox.button(QDialogButtonBox.Close)

        self.btnSelectInputDir.clicked.connect(self.selectInputDir)
        self.btnSelectOutputFile.clicked.connect(self.selectOutputFile)

        self.manageGui()

    def manageGui(self):
        self.addToCanvasCheck.setChecked(bool(self.settings.value("addToCanvas", True)))

    def selectInputDir(self):
        lastPhotosDir = self.settings.value("lastPhotosDir", ".")
        inputDir = QFileDialog.getExistingDirectory(self,
                                                    self.tr("Select directory with images"),
                                                    lastPhotosDir
                                                   )
        if inputDir == "":
            return

        workDir = QDir(inputDir)
        workDir.setFilter(QDir.Files | QDir.NoSymLinks | QDir.NoDotAndDotDot)
        nameFilter = ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG"]
        workDir.setNameFilters(nameFilter)
        self.inputFiles = workDir.entryList()
        if len(self.inputFiles) == 0:
            QMessageBox.warning(self,
                                self.tr("No images found"),
                                self.tr("There are no supported images in this directory. Please select another one.")
                               )
            self.inputFiles = None
            return

        self.progressBar.setRange(0, len(self.inputFiles))
        self.inputDirEdit.setText(inputDir)
        self.settings.setValue("lastPhotosDir", inputDir)

    def selectOutputFile(self):
        # prepare dialog parameters
        lastDir = self.settings.value("lastShapeDir", ".")
        shpFilter = self.tr("ESRI Shapefiles (*.shp *.SHP)")

        fileDialog = QgsEncodingFileDialog(self,
                                           self.tr("Select output shapefile"),
                                           lastDir,
                                           shpFilter,
                                           ""
                                          )
        fileDialog.setDefaultSuffix(u"shp")
        fileDialog.setFileMode(QFileDialog.AnyFile)
        fileDialog.setAcceptMode(QFileDialog.AcceptSave)
        fileDialog.setConfirmOverwrite(True)

        if not fileDialog.exec_() == QDialog.Accepted:
            return

        outputFile = fileDialog.selectedFiles()
        self.outputEncoding = fileDialog.encoding()

        self.outputFileEdit.setText(outputFile[0])
        self.settings.setValue("lastShapeDir", outputFile[0])

    def reject(self):
        QDialog.reject(self)

    def accept(self):
        outFileName = self.outputFileEdit.text()

        if outFileName == "":
            QMessageBox.warning(self,
                                self.tr("Wrong output file"),
                                self.tr("Output file is improperly defined.\nPlease enter a valid filename and try again.")
                               )
            return

        outFile = QFile(outFileName)
        if outFile.exists():
            if not QgsVectorFileWriter.deleteShapeFile(outFileName):
                QMessageBox.warning(self,
                                    self.tr("Delete error"),
                                    self.tr("Can't delete file %s") % (outFileName)
                                   )
                return

        self.settings.setValue("addToCanvas", self.addToCanvasCheck.isChecked())
        baseDir = self.inputDirEdit.text()

        self.workThread = ImportThread(baseDir,
                                       self.inputFiles,
                                       outFileName,
                                       self.outputEncoding
                                      )
        self.workThread.photoProcessed.connect(self.photoProcessed)
        self.workThread.processingFinished.connect(self.processingFinished)
        self.workThread.processingInterrupted.connect(self.processingInterrupted)

        self.btnOk.setEnabled(False)
        self.btnClose.setText(self.tr("Cancel"))
        self.buttonBox.rejected.disconnect(self.reject)
        self.btnClose.clicked.connect(self.stopProcessing)

        self.workThread.start()

    def photoProcessed(self):
        self.progressBar.setValue(self.progressBar.value() + 1)

    def processingFinished(self, errorsList, hasOutput):
        self.stopProcessing()

        if not hasOutput:
            QMessageBox.warning(self,
                                self.tr("Photo2Shape"),
                                self.tr("There are no geotagged photos in selected directory.\nShapefile was not created.")
                               )
            self.restoreGUI()
            return

        if len(errorsList) > 0:
            msg = self.tr("The following files were not added to shapefile because of errors: <br><br>") + "<br><br>".join(errorsList)
            dlgError = QErrorMessage(self)
            dlgError.showMessage(msg)

        self.writeQml()
        if self.addToCanvasCheck.isChecked():
            self.addLayerToCanvas()

        self.restoreGUI()

    def processingInterrupted(self):
        self.restoreGUI()

    def stopProcessing(self):
        if self.workThread is not None:
            self.workThread.stop()
            self.workThread = None

    def restoreGUI(self):
        self.progressBar.setValue(0)
        self.buttonBox.rejected.connect(self.reject)
        self.btnClose.setText(self.tr("Close"))
        self.btnOk.setEnabled(True)

    def addLayerToCanvas(self):
        layerPath = self.outputFileEdit.text()
        newLayer = QgsVectorLayer(layerPath, QFileInfo(layerPath).baseName(), "ogr")

        if newLayer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(newLayer)
        else:
            QMessageBox.warning(self,
                                self.tr("Photo2Shape"),
                                self.tr("Error loading output shapefile:\n%s") % (layerPath)
                               )

    def writeQml(self):
        outputQml = self.outputFileEdit.text().replace(".shp", ".qml")
        outputFile = QFile(outputQml)
        if outputFile.exists():
            res = QMessageBox.question(self,
                                       self.tr("QML exists"),
                                       self.tr("QML file %s already exists. Overwrite?") % (outputQml),
                                       QMessageBox.Yes | QMessageBox.No
                                      )
            if res != QMessageBox.Yes:
                return
            outputFile.remove()

        templateFile = QFile(":/resources/photos.qml")
        if templateFile.open(QIODevice.ReadOnly):
            if outputFile.open(QIODevice.WriteOnly):
                outputFile.write(templateFile.readAll())
            outputFile.close()
        templateFile.close()
