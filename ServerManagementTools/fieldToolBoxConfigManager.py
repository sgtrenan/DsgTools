# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                              -------------------
        begin                : 2017-02-24
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Philipe Borba - Cartographic Engineer @ Brazilian Army
        email                : borba.philipe@eb.mil.br
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
#General imports
from osgeo import ogr
from uuid import uuid4
import codecs, os, json, binascii

#DSG Tools imports
from DsgTools.Factories.DbFactory.dbFactory import DbFactory 
from DsgTools.CustomWidgets.progressWidget import ProgressWidget
from DsgTools.ServerManagementTools.genericDbManager import GenericDbManager
from DsgTools.Utils.utils import Utils

#PyQt4 imports
from PyQt4.Qt import QObject

class FieldToolBoxConfigManager(GenericDbManager):
    """
    This class manages the customizations on dsgtools databases.
    """
    def __init__(self, serverAbstractDb, dbDict, parentWidget = None):
        super(self.__class__,self).__init__(serverAbstractDb, dbDict, parentWidget = None)
    
    def installFieldToolBoxConfig(self, fieldToolBoxConfigName):
        """
        """
        errorDict = dict()
        settingType = self.getManagerType()
        for dbName in self.dbDict.keys():
            abstractDb = self.dbDict[dbName]
            edgvVersion = abstractDb.getDatabaseVersion()
            recDict = self.adminDb.getRecordFromAdminDb(settingType, fieldToolBoxConfigName, edgvVersion)
            try:
                if not abstractDb.checkIfExistsFieldToolBoxConfigTable():
                    abstractDb.createFieldToolBoxConfigTable()
            except Exception as e:
                errorDict[dbName] = str(e.args[0])
            try:
                abstractDb.db.transaction()
                self.adminDb.db.transaction()
                abstractDb.insertRecordInsidePropertyTable(settingType, recDict, edgvVersion)
                dbOid = abstractDb.getDbOID()
                self.adminDb.insertInstalledRecordIntoAdminDb(settingType, recDict, dbOid)
                abstractDb.db.commit()
                self.adminDb.db.commit()
            except Exception as e:
                abstractDb.db.rollback()
                self.adminDb.db.rollback()
                errorDict[dbName] = str(e.args[0])
        if errorDict != dict():
            errorString = '\n'.join([key+': '+errorDict[key] for key in errorDict.keys()])
            raise Exception(self.tr('Unable installing field toolbox config:\n') + errorString)
    
    def removeFieldToolBoxConfig(self, fieldToolBoxConfigName, edgvVersion, dbNameList):
        pass

    def updateFieldToolBoxConfig(self, customizationName):
        pass

    def validateJsonProfile(self, inputJsonDict):
        """
        1. Validates each key and value in inputJsonDict;
        2. If input is ok, returns True;
        3. If one piece of json is not valid, returns False.
        This validator does not validate the name of classes or names of categories. It only checks the format of dsgtools json profile.
        """
        #TODO
        return True
    
    def getPropertyPerspectiveDict(self, viewType = 'property'):
        """
        Gets a dict in the format:
        if viewType == 'customization': {customizationName: ['-list of databases with customization']}
        if viewType == 'database': {databaseName: ['-list of customizations with customization']}
        """
        return self.adminDb.getFieldToolBoxConfigPerspectiveDict(viewType)
