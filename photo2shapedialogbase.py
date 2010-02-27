# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'photo2shapedialogbase.ui'
#
# Created: Sat Feb 27 13:02:58 2010
#      by: PyQt4 UI code generator 4.5.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Photo2ShapeDialog(object):
    def setupUi(self, Photo2ShapeDialog):
        Photo2ShapeDialog.setObjectName("Photo2ShapeDialog")
        Photo2ShapeDialog.resize(403, 176)
        self.verticalLayout = QtGui.QVBoxLayout(Photo2ShapeDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QtGui.QLabel(Photo2ShapeDialog)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.inputDirEdit = QtGui.QLineEdit(Photo2ShapeDialog)
        self.inputDirEdit.setObjectName("inputDirEdit")
        self.horizontalLayout.addWidget(self.inputDirEdit)
        self.selectInputDirButton = QtGui.QPushButton(Photo2ShapeDialog)
        self.selectInputDirButton.setObjectName("selectInputDirButton")
        self.horizontalLayout.addWidget(self.selectInputDirButton)
        self.formLayout.setLayout(0, QtGui.QFormLayout.FieldRole, self.horizontalLayout)
        self.label_2 = QtGui.QLabel(Photo2ShapeDialog)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.outputFileEdit = QtGui.QLineEdit(Photo2ShapeDialog)
        self.outputFileEdit.setObjectName("outputFileEdit")
        self.horizontalLayout_2.addWidget(self.outputFileEdit)
        self.selectOutputFileButton = QtGui.QPushButton(Photo2ShapeDialog)
        self.selectOutputFileButton.setObjectName("selectOutputFileButton")
        self.horizontalLayout_2.addWidget(self.selectOutputFileButton)
        self.formLayout.setLayout(1, QtGui.QFormLayout.FieldRole, self.horizontalLayout_2)
        self.verticalLayout.addLayout(self.formLayout)
        self.progressBar = QtGui.QProgressBar(Photo2ShapeDialog)
        self.progressBar.setProperty("value", QtCore.QVariant(0))
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)
        self.addToCanvasCheck = QtGui.QCheckBox(Photo2ShapeDialog)
        self.addToCanvasCheck.setObjectName("addToCanvasCheck")
        self.verticalLayout.addWidget(self.addToCanvasCheck)
        self.buttonBox = QtGui.QDialogButtonBox(Photo2ShapeDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Photo2ShapeDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Photo2ShapeDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Photo2ShapeDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Photo2ShapeDialog)

    def retranslateUi(self, Photo2ShapeDialog):
        Photo2ShapeDialog.setWindowTitle(QtGui.QApplication.translate("Photo2ShapeDialog", "Images to shapefile", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Photo2ShapeDialog", "Directory with images", None, QtGui.QApplication.UnicodeUTF8))
        self.selectInputDirButton.setText(QtGui.QApplication.translate("Photo2ShapeDialog", "Browse", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Photo2ShapeDialog", "Output shapefile", None, QtGui.QApplication.UnicodeUTF8))
        self.selectOutputFileButton.setText(QtGui.QApplication.translate("Photo2ShapeDialog", "Browse", None, QtGui.QApplication.UnicodeUTF8))
        self.addToCanvasCheck.setText(QtGui.QApplication.translate("Photo2ShapeDialog", "Add result to canvas", None, QtGui.QApplication.UnicodeUTF8))

