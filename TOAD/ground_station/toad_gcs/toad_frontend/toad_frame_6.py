# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/toad_frame_6.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_toad_frame_6(object):
    def setupUi(self, toad_frame_6):
        toad_frame_6.setObjectName(_fromUtf8("toad_frame_6"))
        toad_frame_6.resize(400, 300)
        toad_frame_6.setStyleSheet(_fromUtf8("background-color: rgb(0, 170, 255);"))
        toad_frame_6.setFrameShape(QtGui.QFrame.StyledPanel)
        toad_frame_6.setFrameShadow(QtGui.QFrame.Raised)
        self.verticalLayout = QtGui.QVBoxLayout(toad_frame_6)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.title_label = QtGui.QLabel(toad_frame_6)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.title_label.setFont(font)
        self.title_label.setObjectName(_fromUtf8("title_label"))
        self.verticalLayout.addWidget(self.title_label)
        self.frame = toad_frame(toad_frame_6)
        self.frame.setAutoFillBackground(False)
        self.frame.setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 255);"))
        self.frame.setObjectName(_fromUtf8("frame"))
        self.verticalLayout.addWidget(self.frame)

        self.retranslateUi(toad_frame_6)
        QtCore.QMetaObject.connectSlotsByName(toad_frame_6)

    def retranslateUi(self, toad_frame_6):
        toad_frame_6.setWindowTitle(_translate("toad_frame_6", "Frame", None))
        self.title_label.setText(_translate("toad_frame_6", "TOAD 6", None))

from .toad_frame import toad_frame

class toad_frame_6(QtGui.QFrame, Ui_toad_frame_6):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QFrame.__init__(self, parent, f)

        self.setupUi(self)

