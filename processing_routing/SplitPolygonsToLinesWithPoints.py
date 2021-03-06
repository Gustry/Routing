# -*- coding: utf-8 -*-

from qgis.core import QGis, QgsFeature, QgsFeatureRequest, QgsGeometry

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.parameters import ParameterVector
from processing.core.outputs import OutputVector
from processing.tools import dataobjects
from processing.tools.vector import spatialindex, features


class SplitPolygonsToLinesWithPoints(GeoAlgorithm):

    POINTS_LAYER = 'POINTS_LAYER'
    POLYGONS_LAYER = 'POLYGONS_LAYER'
    OUTPUT = 'OUTPUT'

    def defineCharacteristics(self):
        self.name = 'SplitPolygonsToLinesWithPoints'
        self.group = 'Vector geometry tools'

        self.addParameter(ParameterVector(self.POLYGONS_LAYER,
            self.tr('Polygons layer'), [ParameterVector.VECTOR_TYPE_POLYGON]))
        self.addParameter(ParameterVector(
            self.POINTS_LAYER, 'Points layer', [ParameterVector.VECTOR_TYPE_POINT], False))

        self.addOutput(OutputVector(self.OUTPUT, self.tr('Output layer')))

    def processAlgorithm(self, progress):
        layer_poly = dataobjects.getObjectFromUri(
            self.getParameterValue(self.POLYGONS_LAYER))

        points_layer = dataobjects.getObjectFromUri(
            self.getParameterValue(self.POINTS_LAYER))

        writer = self.getOutputFromName(self.OUTPUT).getVectorWriter(
            layer_poly.pendingFields().toList(),
            QGis.WKBLineString,
            layer_poly.crs())

        polygons_spatial_index = spatialindex(layer_poly)

        # cuttings : dict QgsPoint : id
        cutting = {}
        for f in features(points_layer):
            point = f.geometry().asPoint()
            results = polygons_spatial_index.nearestNeighbor(point, 5)
            min = None
            f_id = None
            for result in results:
                request = QgsFeatureRequest().setFilterFid(result)
                poly = layer_poly.getFeatures(request).next()
                dist = poly.geometry().distance(f.geometry())
                if dist < min or min is None:
                    min = dist
                    f_id = poly.id()
            cutting[point] = f_id

        for f in features(layer_poly):
            feature = QgsFeature()
            attributes = f.attributes()
            geometry = f.geometry()
            polyline = geometry.asPolygon()[0]

            if geometry.isMultipart() or geometry.wkbType() != QGis.WKBPolygon:
                raise GeoAlgorithmExecutionException('multi')

            for ring in geometry.asPolygon()[1:]:
                ring_feature = QgsFeature()
                ring_feature.setAttributes(attributes)
                ring_feature.setGeometry(QgsGeometry.fromPolyline(ring))
                writer.addFeature(ring_feature)

            if f.id() not in cutting.values():
                feature.setGeometry(QgsGeometry.fromPolyline(polyline))
                feature.setAttributes(attributes)
                writer.addFeature(feature)
            else:

                # Getting a list of QgsPoint which will cut this polygon.
                list_point = [
                    point for point, id in cutting.iteritems() if id == f.id()]

                #print polygone
                new_geometries = []
                for i, point in enumerate(list_point):
                    if i == 0:
                        # First loop, we need to transform the polygon to a
                        # polyline at the good vertex.
                        result = geometry.closestSegmentWithContext(point)
                        new_point = result[1]
                        index = result[2]
                        polyline.insert(index, new_point)
                        polyline.insert(index, new_point)
                        polyline.pop(0)
                        polyline = polyline[index:] + polyline[:index]
                        new_geometries.append(
                            QgsGeometry.fromPolyline(polyline))
                    else:
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
                        l = len(polyline)
                        temp_geometries = []
                        temp_geometries.append(
                            QgsGeometry.fromPolyline(polyline[:index+1]))
                        temp_geometries.append(
                            QgsGeometry.fromPolyline(polyline[-(l-index):]))

                        # Deleting the old geometry which has been splitted
                        i = new_geometries.index(closest_geom)
                        new_geometries.pop(i)

                        for geom in temp_geometries:
                            if geom.length() > 0:
                                new_geometries.append(geom)

                for geom in new_geometries:
                    feature.setGeometry(geom)
                    feature.setAttributes(attributes)
                    writer.addFeature(feature)

        del writer