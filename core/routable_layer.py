# -*- coding: utf-8 -*-

from processing import features
from processing.tools import vector
from qgis.core import QgsVectorLayer, QgsFeatureRequest, QgsFeature, QgsGeometry

class RoutableLayer:

    def __init__(self, roads_layer, flood_layer):
        self.roads_layer = roads_layer
        self.roads_index = vector.spatialindex(self.roads_layer)
        self.flood_layer = flood_layer
        self.flood_index = vector.spatialindex(self.flood_layer)
        self.routable_layer = QgsVectorLayer("LineString", "Line", "memory")
        self.routable_layer_dp = self.routable_layer.dataProvider()
        self.unroutable_layer = QgsVectorLayer("LineString", "Line", "memory")
        self.unroutable_layer_dp = self.unroutable_layer.dataProvider()

    def compute_without_index(self):
        import pydevd
        pydevd.settrace('localhost', port=8888, stdoutToServer=True, stderrToServer=True)

        for road_feature in features(self.roads_layer):
            road_geom = road_feature.geometry()

            intersects = self.flood_index.intersects(road_geom.boundingBox())
            if len(intersects) > 0:

                geom_diff = QgsGeometry(road_geom)
                diff_feature = QgsFeature()
                diff_feature.setAttributes(road_feature.attributes())

                geom_inter = QgsGeometry()
                inter_feature = QgsFeature()
                inter_feature.setAttributes(road_feature.attributes())

                for i in intersects:
                    request = QgsFeatureRequest().setFilterFid(i)
                    flood_feature = self.flood_layer.getFeatures(request).next()
                    flood_geom = flood_feature.geometry()
                    if geom_diff.intersects(flood_geom):
                        geom_diff = geom_diff.difference(flood_geom)
                        geom_inter = road_geom.intersection(flood_geom)

                inter_feature.setGeometry(geom_inter)
                self.unroutable_layer_dp.addFeatures([inter_feature])
                diff_feature.setGeometry(geom_diff)
                self.routable_layer_dp.addFeatures([diff_feature])

            else:
                self.routable_layer_dp.addFeatures([road_feature])

        self.routable_layer_dp.updateExtents()
        self.unroutable_layer_dp.updateExtents()
        return self.unroutable_layer, self.routable_layer
