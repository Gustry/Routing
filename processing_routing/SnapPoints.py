# -*- coding: utf-8 -*-

from qgis.core import QGis, QgsFeature, QgsGeometry, QgsField, QgsSnappingUtils
from PyQt4.QtCore import QVariant
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterVector, ParameterBoolean, ParameterSelection, ParameterNumber
from processing.core.outputs import OutputVector
from processing.tools.dataobjects import getObjectFromUri
from processing.tools import vector


class SnapPoints(GeoAlgorithm):

    POINTS = 'POINTS'
    LAYER = 'LAYER'
    SNAP_TYPE = 'SNAP_TYPE'
    TOLERANCE = 'TOLERANCE'
    INTERSECTIONS = 'INTERSECTIONS'
    UNIT = 'UNIT'
    SNAPPED = 'SNAPPED'
    OUTPUT = 'OUTPUT'

    def defineCharacteristics(self):
        self.name = "Snap points to a layer"
        self.group = "Vector creation tools"

        self.addParameter(ParameterVector(
            self.POINTS, 'Points to snap', [ParameterVector.VECTOR_TYPE_POINT], False))
        self.addParameter(ParameterVector(
            self.POINTS, 'Snap on', [ParameterVector.VECTOR_TYPE_ANY], False))
        self.addParameter(ParameterSelection(
            self.SNAP_TYPE, 'Type', ['SnapToVertex', 'SnapToSegment', 'SnapToVertexAndSegment']))
        self.addParameter(ParameterNumber(
            self.TOLERANCE, 'Tolerance', minValue=0, default=0))
        self.addParameter(ParameterSelection(
            self.UNIT, 'Unit', ['LayerUnits', 'Pixels', 'ProjectUnits']))
        self.addParameter(ParameterBoolean(
            self.INTERSECTIONS, 'Snap to intersections', False))
        self.addParameter(ParameterBoolean(
            self.SNAPPED,
            'Add an attribute if it has been snapped',
            False))

        self.addOutput(OutputVector(self.OUTPUT, 'Output'))

    def processAlgorithm(self, progress):
        points_layer = self.getParameterValue(self.POINTS)
        points_layer = getObjectFromUri(points_layer)

        add_attribute = self.getParameterValue(self.SNAPPED)

        fields = points_layer.dataProvider().fields()

        if add_attribute:
            fields.append(QgsField('snapped', QVariant.String))

        writer = self.getOutputFromName(self.OUTPUT).getVectorWriter(
            fields,
            QGis.WKBPoint,
            points_layer.crs())

        snapper = QgsSnappingUtils()


        snapping_type = QgsSnapper.SnapToSegment
        tolerance = 1
        unit = QgsTolerance.LayerUnits
        layer_config = QgsSnappingUtils.LayerConfig(layer_edge, snapping_type, tolerance, unit)
        snapper.setLayers([layer_config])
        snap_mode = QgsSnappingUtils.SnapAdvanced
        snapper.setSnapToMapMode(snap_mode)

        for feature in vector.features(points_layer):
            f = QgsFeature()
            attributes = feature.attributes()
            result = snapper.snapToMap(feature.geometry().asPoint())
            if result.type() == 2:
                f.setGeometry(QgsGeometry.fromPoint(result.point()))
                if add_attribute:
                    attributes.append('True')
            else:
                f.setGeometry(feature.geometry())
                if add_attribute:
                    attributes.append('False')
            f.setAttributes(attributes)
            writer.addFeature(f)
        del writer
