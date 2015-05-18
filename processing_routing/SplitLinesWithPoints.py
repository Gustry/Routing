# -*- coding: utf-8 -*-

from qgis.core import QGis, QgsFeature, QgsFeatureRequest, QgsGeometry
from qgis.utils import iface
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import \
    GeoAlgorithmExecutionException
from processing.core.parameters import ParameterVector
from processing.core.outputs import OutputVector
from processing.tools.dataobjects import getObjectFromUri
from processing.tools.vector import spatialindex, features


class SplitLinesWithPoints(GeoAlgorithm):

    LINES = 'LINES'
    POINTS = 'POINTS'
    OUTPUT = 'OUTPUT'

    def defineCharacteristics(self):
        self.name = "Split line with point"
        self.group = "Vector geometry tools"

        self.addParameter(ParameterVector(self.LINES, 'Lines', [ParameterVector.VECTOR_TYPE_LINE], False))
        self.addParameter(ParameterVector(self.POINTS, 'Points', [ParameterVector.VECTOR_TYPE_POINT], False))

        self.addOutput(OutputVector(self.OUTPUT, 'Output'))

    def processAlgorithm(self, progress):
        lines_layer = self.getParameterValue(self.LINES)
        lines_layer = getObjectFromUri(lines_layer)
        points_layer = self.getParameterValue(self.POINTS)
        points_layer = getObjectFromUri(points_layer)

        writer = self.getOutputFromName(self.OUTPUT).getVectorWriter(
            lines_layer.dataProvider().fields(),
            QGis.WKBLineString,
            lines_layer.crs())

        idx_lines = spatialindex(lines_layer)
        cutting = {}
        for f in features(points_layer):
            point = f.geometry().asPoint()
            results = idx_lines.nearestNeighbor(point, 1)
            request = QgsFeatureRequest().setFilterFid(results[0])
            cutting[point] = lines_layer.getFeatures(request).next().id()

        for f in features(lines_layer):
            if f.id() in cutting.values():
                list_point = [point for point, id in cutting.iteritems() if id == f.id()]
                attributes = f.attributes()
                # geometry = f.geometry()
                # polyline = geometry.asPolyline()

                '''
                if len(list_point) == 1:
                    new_polylines = []
                    result = geometry.closestSegmentWithContext(point)
                    new_point = result[1]
                    index = result[2]
                    polyline.insert(index, new_point)
                    new_polylines.append(polyline[0:index+1])
                    new_polylines.append(polyline[-index-1:])

                    for new_polyline in new_polylines:
                        new_feature = QgsFeature()
                        new_feature.setAttributes(attributes)
                        new_feature.setGeometry(
                            QgsGeometry.fromPolyline(new_polyline))
                        writer.addFeature(new_feature)

                else:
                '''

                new_geometries = [f.geometry()]
                for point in list_point:

                    min = None
                    closest_geom = None
                    for geom in new_geometries:
                        dist = geom.distance(QgsGeometry.fromPoint(point))
                        if dist <= min or min is None:
                            min = dist
                            closest_geom = geom

                    result = closest_geom.closestSegmentWithContext(point)
                    new_point = result[1]
                    index = result[2]
                    polyline = closest_geom.asPolyline()
                    polyline.insert(index, new_point)
                    i = new_geometries.index(closest_geom)
                    new_geometries.pop(i)
                    temp_geometries = []
                    temp_geometries.append(
                        QgsGeometry.fromPolyline(polyline[0:index+1]))
                    temp_geometries.append(
                        QgsGeometry.fromPolyline(polyline[-index-1:]))

                    for geom in temp_geometries:
                        if geom.length() > 0:
                            new_geometries.append(geom)

                for geom in new_geometries:
                    new_feature = QgsFeature()
                    new_feature.setAttributes(attributes)
                    new_feature.setGeometry(geom)
                    writer.addFeature(new_feature)

            else:
                writer.addFeature(f)

        del writer