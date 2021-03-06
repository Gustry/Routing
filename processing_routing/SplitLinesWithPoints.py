# -*- coding: utf-8 -*-

from qgis.core import QGis, QgsFeature, QgsFeatureRequest, QgsGeometry
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.parameters import ParameterVector
from processing.core.outputs import OutputVector
from processing.tools.dataobjects import getObjectFromUri
from processing.tools.vector import spatialindex, features


class SplitLinesWithPoints(GeoAlgorithm):

    LINES = 'LINES'
    POINTS = 'POINTS'
    OUTPUT = 'OUTPUT'

    def defineCharacteristics(self):
        self.name = "Split lines with points"
        self.group = "Vector geometry tools"

        self.addParameter(ParameterVector(
            self.LINES, 'Lines', [ParameterVector.VECTOR_TYPE_LINE], False))
        self.addParameter(ParameterVector(
            self.POINTS, 'Points', [ParameterVector.VECTOR_TYPE_POINT], False))

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
            results = idx_lines.nearestNeighbor(point, 5)
            min = None
            f_id = None
            for result in results:
                request = QgsFeatureRequest().setFilterFid(result)
                line = lines_layer.getFeatures(request).next()
                dist = line.geometry().distance(f.geometry())
                if dist < min or min is None:
                    min = dist
                    f_id = line.id()
            cutting[point] = f_id

        for f in features(lines_layer):
            if f.id() in cutting.values():
                list_point = [
                    point for point, id in cutting.iteritems() if id == f.id()]
                attributes = f.attributes()

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
                    temp_geometries = []

                    if closest_geom.isMultipart():
                        multipolyline = closest_geom.asMultiPolyline()
                        for i in range(len(multipolyline)):
                            l = len(multipolyline[i])
                            if index > l:
                                index -= l
                            else:
                                multipolyline[i].insert(index, new_point)
                                break

                        temp1 = []
                        temp2 = []
                        index = result[2]
                        sum = 0
                        for i in range(len(multipolyline)):
                            l = len(multipolyline[i])
                            if sum + l < index:
                                temp1.append(multipolyline[i])
                            elif (sum < index) and (sum + l) > index:
                                temp1.append(
                                    multipolyline[i][:(index-sum) + 1])
                                if sum == 0:
                                    temp2.append(multipolyline[i][index:])
                                else:
                                    temp2.append(multipolyline[i][-sum:])
                            else:
                                temp2.append(multipolyline[i])
                            sum += l
                        temp_geometries.append(
                            QgsGeometry.fromMultiPolyline(temp1))
                        temp_geometries.append(
                            QgsGeometry.fromMultiPolyline(temp2))

                    else:
                        polyline = closest_geom.asPolyline()
                        polyline.insert(index, new_point)
                        l = len(polyline)
                        temp_geometries.append(
                            QgsGeometry.fromPolyline(polyline[:index+1]))
                        temp_geometries.append(
                            QgsGeometry.fromPolyline(polyline[-(l-index):]))

                    i = new_geometries.index(closest_geom)
                    new_geometries.pop(i)

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
