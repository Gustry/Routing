# -*- coding: utf-8 -*-
from tempfile import NamedTemporaryFile
from processing import features
from processing.tools import vector
from qgis.core import QgsVectorLayer, QgsFeatureRequest, QgsFeature, QgsGeometry
from qgis.analysis import QgsOverlayAnalyzer

class RoutableLayer:

    def __init__(self, roads_layer, flood_layer, delete_inner_rings=True):
        self.roads_layer = roads_layer
        self.roads_index = vector.spatialindex(self.roads_layer)
        self.flood_layer = flood_layer
        self.flood_index = vector.spatialindex(self.flood_layer)
        self.delete_inner_rings = delete_inner_rings
        self.routable_layer = QgsVectorLayer("LineString", "Line", "memory")
        self.routable_layer_dp = self.routable_layer.dataProvider()
        self.exits_layer = QgsVectorLayer("Points", "Line", "memory")
        self.exits_layer_dp = self.exits_layer.dataProvider()

    def compute_without_index(self):

        for road_feature in features(self.roads_layer):
            road_geom = road_feature.geometry()

            intersects = self.flood_index.intersects(road_geom.boundingBox())
            print intersects
            if intersects:
                geom_diff = QgsGeometry(road_geom)
                diff_feature = QgsFeature()
                diff_feature.setAttributes(road_feature.attributes())
                diff_feature.setGeometry(geom_diff)

                for i in intersects:
                    request = QgsFeatureRequest().setFilterFid(i)
                    flood_feature = self.flood_layer.getFeatures(request).next()
                    flood_geom = flood_feature.geometry()
                    if geom_diff.intersects(flood_geom):
                        geom_diff = geom_diff.difference(flood_geom)

                self.routable_layer_dp.addFeatures([diff_feature])
            else:
                self.routable_layer_dp.addFeatures([road_feature])

        self.routable_layer_dp.updateExtents()
        self.exits_layer_dp.updateExtents()
        return self.exits_layer, self.routable_layer

    def compute(self):
        for flood_feature in features(self.flood_layer):
            flood_geom = flood_feature.geometry()

            if self.delete_inner_rings:
                flood_geom = self._delete_inner_ring(flood_geom)

            lines = self.spatial_index.intersects(flood_geom.boundingBox())

            if len(lines) > 0:  # has intersections
                for i in lines:
                    request = QgsFeatureRequest().setFilterFid(i)
                    road_feature = self.roads_layer.getFeatures(request).next()
                    road_geom = road_feature.geometry()

                    if not flood_geom.intersects(road_geom):
                        self.routable_layer_dp.addFeatures([road_feature])
                    else:

                        diff_feature = QgsFeature()
                        geom_diff = road_geom.difference(flood_geom)
                        diff_feature.setAttributes(road_feature.attributes())
                        diff_feature.setGeometry(
                            road_geom.difference(flood_geom))
                        self.routable_layer_dp.addFeatures([diff_feature])

                        geom_inter = road_geom.intersection(flood_geom)

                        if geom_inter.touches(geom_diff):
                            for part in geom_inter.asGeometryCollection():
                                polyline = part.asPolyline()
                                if len(polyline):
                                    for point in [polyline[0], polyline[-1]]:
                                        point_geom = QgsGeometry.fromPoint(point)

                                        if point_geom.touches(geom_diff):
                                            exit_feature = QgsFeature()
                                            exit_feature.setGeometry(point_geom)
                                            self.exits_layer_dp.addFeatures([exit_feature])

            else:
                self.routable_layer_dp.addFeatures([road_feature])

            # Add rings and cut to each exit
            '''
            flood_polygon = flood_geom.asPolygon()
            for ring in flood_polygon:
                ring_geom = QgsGeometry.fromPolyline(ring)
                print ring_geom
                for i, vertex in enumerate(ring):
                    print vertex
            '''

        self.routable_layer_dp.updateExtents()
        self.exits_layer_dp.updateExtents()
        return self.exits_layer, self.routable_layer

    @staticmethod
    def _delete_inner_ring(geometry):
        i = 0
        while True:
            i += 1
            if not geometry.deleteRing(i):
                return geometry