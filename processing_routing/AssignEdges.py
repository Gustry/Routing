# -*- coding: utf-8 -*-

from Routing.core.middle import *
from qgis.core import QGis, QgsFeature, QgsFeatureRequest, QgsGeometry, QgsField, QgsPoint
from PyQt4.QtCore import QVariant
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.parameters import ParameterVector, ParameterTableField
from processing.core.outputs import OutputVector
from processing.tools.dataobjects import getObjectFromUri
from processing.tools.vector import spatialindex, features


class AssignEdges(GeoAlgorithm):

    LINES = 'LINES'
    POINTS = 'POINTS'
    FIELD = 'FIELD'
    OUTPUT = 'OUTPUT'

    def defineCharacteristics(self):
        self.name = "Allocating edges"
        self.group = "Routing"

        self.addParameter(ParameterVector(
            self.LINES, 'Lines', [ParameterVector.VECTOR_TYPE_LINE], False))
        self.addParameter(ParameterVector(
            self.POINTS, 'Points', [ParameterVector.VECTOR_TYPE_POINT], False))
        self.addParameter(ParameterTableField(
            self.FIELD, self.tr('IDP ID'), self.POINTS))

        self.addOutput(OutputVector(self.OUTPUT, 'Output'))

    def processAlgorithm(self, progress):
        lines_layer = self.getParameterValue(self.LINES)
        self.lines_layer = getObjectFromUri(lines_layer)
        points_layer = self.getParameterValue(self.POINTS)
        self.points_layer = getObjectFromUri(points_layer)
        field = self.getParameterValue(self.FIELD)
        index_field = self.points_layer.fieldNameIndex(field)

        fields = [QgsField(field, QVariant.Int)]

        writer = self.getOutputFromName(self.OUTPUT).getVectorWriter(
            fields,
            QGis.WKBLineString,
            self.lines_layer.crs())

        self.idx_points = spatialindex(self.points_layer)

        for edge in features(self.lines_layer):
            geometry = edge.geometry()

            point_start = QgsGeometry.fromPoint(
                QgsPoint(geometry.asPolyline()[0]))
            feature_start = self.get_nearest_exit(point_start)
            point_end = QgsGeometry.fromPoint(
                QgsPoint(geometry.asPolyline()[-1]))
            feature_end = self.get_nearest_exit(point_end)

            idp_start = feature_start.attributes()[index_field]
            idp_end = feature_end.attributes()[index_field]

            if idp_start == idp_end:
                edge.setAttributes([idp_start])
                writer.addFeature(edge)
            else:
                geom = geometry.asPolyline()
                split = split_middle(geom)
                for idp, part in zip([idp_start, idp_end], split):
                    f = QgsFeature()
                    f.setAttributes([idp])
                    new_geom = [QgsPoint(p[0], p[1]) for p in part]
                    f.setGeometry(QgsGeometry.fromPolyline(new_geom))
                    writer.addFeature(f)

        del writer

    def get_nearest_exit(self, point):
        results = self.idx_points.nearestNeighbor(point.asPoint(), 5)
        min = None
        feature = None

        for result in results:
            request = QgsFeatureRequest().setFilterFid(result)
            f = self.points_layer.getFeatures(request).next()
            dist = f.geometry().distance(point)
            if dist < min or min is None:
                min = dist
                feature = f
        return feature