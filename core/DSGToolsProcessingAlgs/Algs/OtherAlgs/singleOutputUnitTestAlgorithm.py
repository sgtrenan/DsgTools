# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                              -------------------
        begin                : 2019-08-19
        git sha              : $Format:%H$
        copyright            : (C) 2019 by João P. Esperidião - Cartographic Engineer @ Brazilian Army
        email                : esperidiao.joao@eb.mil.br
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

import json

from qgis.PyQt.Qt import QVariant
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterEnum,
                       QgsProcessingException,
                       QgsCoordinateReferenceSystem,
                       QgsFields,
                       QgsField,
                       QgsWkbTypes)

from DsgTools.tests.test_ValidationAlgorithms import Tester

class SingleOutputUnitTestAlgorithm(QgsProcessingAlgorithm):
    __description__ = """Runs unit tests for a set of DSGTools algorithms that""" \
                      """has single output - in-place modified or otherwise."""
    AVAILABLE_ALGS = [
        # identification algs
        "dsgtools:identifyoutofboundsangles", "dsgtools:identifyoutofboundsanglesincoverage",
        "dsgtools:identifygaps", "dsgtools:identifyandfixinvalidgeometries",
        "dsgtools:identifyduplicatedfeatures", "dsgtools:identifyduplicatedgeometries",
        "dsgtools:identifyduplicatedlinesoncoverage", "dsgtools:identifysmalllines",
        "dsgtools:identifyduplicatedpolygonsoncoverage", "dsgtools:identifysmallpolygons",
        "dsgtools:identifydangles", "dsgtools:identifyduplicatedpointsoncoverage",
        "dsgtools:identifyoverlaps",
        # correction algs
        "dsgtools:removeduplicatedfeatures", "dsgtools:removeduplicatedgeometries",
        "dsgtools:removesmalllines", "dsgtools:removesmallpolygons",
        # manipulation algs
        "dsgtools:lineonlineoverlayer", "dsgtools:mergelineswithsameattributeset",
        "dsgtools:overlayelementswithareas", "dsgtools:deaggregategeometries",
        "dsgtools:dissolvepolygonswithsameattributes", "dsgtools:removeemptyandupdate",
        "dsgtools:snaplayeronlayer",
        # network algs
        "dsgtools:adjustnetworkconnectivity"
    ]
    INPUT_ALGS = 'INPUT_ALGS'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super(SingleOutputUnitTestAlgorithm, self).__init__()

    def initAlgorithm(self, config=None):
        """
        Parameter setting.
        """
        self.addParameter(
            QgsProcessingParameterEnum(
                self.INPUT_ALGS,
                self.tr('Algorithms to be tested:'),
                options=self.AVAILABLE_ALGS,
                optional=False,
                allowMultiple=True

            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("DSGTools Algorithms Unit Tests")
            )
        )
        
    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised 
        (e.g. must be ASCII). The name should be unique within each provider.
        Names should contain lowercase alphanumeric characters only and no 
        spaces or other formatting characters.
        """
        return 'singleoutputunittest'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Single Output Algorithms Unit Test')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Other Algorithms')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'DSGTools: Other Algorithms'

    def tr(self, string):
        return QCoreApplication.translate('SingleOutputUnitTestAlgorithm', string)

    def createInstance(self):
        """
        Gets a new instance of algotithm object.
        """
        return SingleOutputUnitTestAlgorithm()

    def getFields(self):
        """
        Gets all fields for output layer.
        """
        fields = QgsFields()
        fields.append(QgsField('node_type', QVariant.String))
        fields.append(QgsField('layer', QVariant.String))
        return fields

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        if not self.INPUT_ALGS:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.INPUT_ALGS)
            )
        algsOutput, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, self.getFields(),
            QgsWkbTypes.NoGeometry, QgsCoordinateReferenceSystem('EPSG:4326')
        )
        tester = Tester()
        size = len(self.INPUT_ALGS)
        for i, alg in enumerate(self.INPUT_ALGS):
            if feedback.isCanceled():
                break
            feedback.pushInfo(self.tr("Testing {alg}'s...").format(alg=alg))
            try:
                # if any test fails, an exception is raised
                tester.testAlg(alg)
                msg = self.tr("All tests are OK.")
                feedback.pushInfo(msg)
            except Exception as e:
                msg = str(e)
                feedback.pushInfo(msg)
        return { self.OUTPUT : dest_id }
