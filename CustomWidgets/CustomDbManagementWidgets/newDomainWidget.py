# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                              -------------------
        begin                : 2017-01-04
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Philipe Borba - Cartographic Engineer @ Brazilian Army
        email                : borba@dsg.eb.mil.br
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os

from qgis.core import QgsMessageLog

# Qt imports
from PyQt4 import QtGui, uic, QtCore
from PyQt4.QtCore import pyqtSlot, pyqtSignal, QSettings
from PyQt4.QtSql import QSqlQuery

# DSGTools imports
from DsgTools.ServerTools.viewServers import ViewServers
from DsgTools.Factories.SqlFactory.sqlGeneratorFactory import SqlGeneratorFactory
from DsgTools.Factories.DbFactory.dbFactory import DbFactory
from DsgTools.CustomWidgets.CustomDbManagementWidgets.addAttributeWidget import AddAttributeWidget
from DsgTools.PostgisCustomization.CustomJSONTools.customJSONBuilder import CustomJSONBuilder
from PyQt4.Qt import QTableWidgetItem, QLineEdit, QToolTip

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'newDomainWidget.ui'))

class ValidatedItemDelegate(QtGui.QStyledItemDelegate):
    def createEditor(self, widget, option, index):
        if not index.isValid():
            return 0
        if index.column() == 0: #only on the cells in the first column
            editor = QtGui.QLineEdit(widget)
            validator = QtGui.QRegExpValidator(QtCore.QRegExp("[0-9]*"), editor)
            editor.setValidator(validator)
            return editor
        elif index.column() == 1:
            editor = QtGui.QLineEdit(widget)
            editor.setPlaceholderText(self.tr('Enter a value.'))
            return editor
        return super(ValidatedItemDelegate, self).createEditor(widget, option, index)

class NewDomainWidget(QtGui.QWidget, FORM_CLASS):
    def __init__(self, abstractDb, parent = None):
        """Constructor."""
        super(self.__class__, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self) 
        header = self.tableWidget.horizontalHeader()
        header.setStretchLastSection(True)
        regex = QtCore.QRegExp('[a-z][a-z\_]*')
        validator = QtGui.QRegExpValidator(regex, self.domainNameLineEdit)
        self.domainNameLineEdit.setValidator(validator)
        self.abstractDb = abstractDb
        self.jsonBuilder = CustomJSONBuilder()
        self.tableWidget.setItemDelegate(ValidatedItemDelegate())
        self.oldBackground = None
    
    @pyqtSlot()
    def on_domainNameLineEdit_editingFinished(self):
        text = self.domainNameLineEdit.text()
        while text[-1] == '_':
            self.domainNameLineEdit.setText(text[0:-1])
            text = text[0:-1]
    
    @pyqtSlot(str)
    def on_domainNameLineEdit_textEdited(self, newText):
        if len(newText) > 1:
            if newText[-1] == '_' and newText[-2] == '_':
                    self.domainNameLineEdit.setText(newText[0:-1])
    
    @pyqtSlot(bool)
    def on_addValuePushButton_clicked(self):
        index = self.tableWidget.rowCount()
        self.tableWidget.insertRow(index)
        codeItem = QtGui.QTableWidgetItem('')
        valueItem = QtGui.QTableWidgetItem('')
        self.tableWidget.setItem(self.tableWidget.rowCount()-1, 0, codeItem)
        self.tableWidget.setItem(self.tableWidget.rowCount()-1, 1, valueItem)
        if index == 0:
            self.oldBackground = self.tableWidget.item(0,0).background()     
    
    @pyqtSlot(bool)
    def on_removeValuePushButton_clicked(self):
        selected = self.tableWidget.selectedIndexes()
        rowList = [i.row() for i in selected]
        rowList.sort(reverse=True)
        for row in rowList:
            self.tableWidget.removeRow(row)
    
    @pyqtSlot(QTableWidgetItem)
    def on_tableWidget_itemChanged(self, widgetItem):
        if self.checkNull(widgetItem):
            return
        if self.tableWidget.currentColumn() == 0:
            self.checkUnique(widgetItem)
    
    def checkNull(self, widgetItem):
        if widgetItem.text() == '':
            widgetItem.setToolTip(self.tr('Enter a value!'))
            return True
        else:
            widgetItem.setToolTip('')
            return False
    
    def checkUnique(self, widgetItem):
        currentValue = widgetItem.text() 
        itemList = []
        for i in range(self.tableWidget.rowCount()):
            if i <> widgetItem.row():
                curItem = self.tableWidget.item(i, 0)
                itemList.append(curItem.text())
        if currentValue in itemList:
            widgetItem.setBackground(QtGui.QColor(230,124,127))
            self.tableWidget.setCurrentCell(widgetItem.row(), 0)
            widgetItem.setToolTip(self.tr('Code value already entered.'))
        else:
            if self.oldBackground:
                widgetItem.setBackground(self.oldBackground)
                widgetItem.setToolTip('')
    
    def getTitle(self):
        return self.title
    
    def setTitle(self, title):
        self.title = title
    
    def validate(self):
        if self.domainNameLineEdit.text() == '':
            return False
        if self.tableHasEmptyValue():
            return False
        if self.tableHasDuplicatedCode():
            return False 
        return True

    def validateDiagnosis(self):
        invalidatedReason = ''
        if self.domainNameLineEdit.text() == '':
            invalidatedReason += self.tr('A domain name must be chosen.\n')
        if self.tableHasEmptyValue():
            invalidatedReason += self.tr('There must be no empty codes or values.\n')
        if self.tableHasEmptyValue():
            invalidatedReason += self.tr('Codes must be unique.\n')
        return invalidatedReason

    def tableHasEmptyValue(self):
        for row in range(self.tableWidget.rowCount()):
            for column in range(self.tableWidget.columnCount()):
                if self.tableWidget.item(row,column).text() == '':
                    return True
        return False
    
    def tableHasDuplicatedCode(self):
        listOfCodes = []
        for row in range(self.tableWidget.rowCount()):
            code = self.tableWidget.item(row,0)
            if code not in listOfCodes:
                listOfCodes.append(code)
            else:
                return True
        return False

    def getJSONTag(self):
        if not self.validate():
            raise Exception(self.tr('Error in domain ')+ self.title + ' : ' + self.validateDiagnosis())
        domainName = self.domainNameLineEdit.text()
        valueDict = dict()
        for row in range(self.tableWidget.rowCount()):
            code = self.tableWidget.item(row,0).text()
            value = self.tableWidget.item(row,1).text()
            valueDict[code] = value
        return [self.jsonBuilder.addDomainTableElement(domainName, valueDict)]