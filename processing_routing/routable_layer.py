# -*- coding: utf-8 -*-

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterVector, ParameterBoolean
from processing.core.outputs import OutputVector
from processing.tools.dataobjects import getObjectFromUri

from qgis.core import (
    QgsVectorFileWriter,
    QGis,
    QgsFeature,
    QgsGeometry,
    QgsPoint,
    QgsRectangle)
import processing


class RoutableLayerGeoAlgorithm(GeoAlgorithm):

    ROADS = 'ROADS'
    FLOOD = 'FLOOD'
    DELETE_RINGS = 'DELETE_RINGS'
    OUTPUT_ROUTABLE_LAYER = 'ROUTABLE_LAYER'
    OUTPUT_EXIT_LAYER = 'EXIT_LAYER'

    def defineCharacteristics(self):
        self.name = "Routable layer"
        self.group = "Routing"

        self.addParameter(ParameterVector(self.ROADS, 'Roads', [ParameterVector.VECTOR_TYPE_LINE], False))
        self.addParameter(ParameterVector(self.FLOOD, 'Flood', [ParameterVector.VECTOR_TYPE_POLYGON], False))
        self.addParameter(ParameterBoolean(self.DELETE_RINGS, 'Delete inner rings', True))

        self.addOutput(OutputVector(self.OUTPUT_ROUTABLE_LAYER, 'Routable layer'))
        self.addOutput(OutputVector(self.OUTPUT_EXIT_LAYER, 'Exit layer'))

    def processAlgorithm(self, progress):
        roads_layer = self.getParameterValue(self.ROADS)
        roads_layer = getObjectFromUri(roads_layer)
        flood_layer = self.getParameterValue(self.FLOOD)
        flood_layer = getObjectFromUri(flood_layer)
        output_routable_layer = self.getOutputValue(self.OUTPUT_ROUTABLE_LAYER)
        output_exit_layer = self.getOutputValue(self.OUTPUT_EXIT_LAYER)
        delete_interior_rings = self.getParameterValue(self.DELETE_RINGS)

        dry_roads_layer = QgsVectorFileWriter(
            output_routable_layer,
            None,
            roads_layer.dataProvider().fields(),
            QGis.WKBLineString ,
            roads_layer.crs()
        )

        exit_layer = QgsVectorFileWriter(
            output_exit_layer,
            None,
            roads_layer.dataProvider().fields(),
            QGis.WKBPoint,
            roads_layer.crs()
        )

        # Testing intersection between flood and roads
        for flood_feature in processing.features(flood_layer):
            flood_geom = flood_feature.geometry()

            if delete_interior_rings:
                i = 0
                while True:
                    i += 1
                    if flood_geom.deleteRing(i):
                        break

            flood_polygon = flood_geom.asPolygon()

            for ring in flood_polygon:
                edge = QgsFeature()
                geom = QgsGeometry.fromPolyline(ring)
                edge.setGeometry(geom)
                dry_roads_layer.addFeature(edge)

            for road_feature in processing.features(roads_layer):
                road_geom = road_feature.geometry()

                # If the road doesn't intersect the flood, we add it directly
                if not road_geom.intersects(flood_geom):
                    dry_roads_layer.addFeature(road_feature)

                else:
                    # We need to take the difference between these two geometries
                    diff = QgsFeature()
                    geom_diff = road_geom.difference(flood_geom)
                    diff.setAttributes(road_feature.attributes())
                    diff.setGeometry(road_geom.difference(flood_geom))
                    dry_roads_layer.addFeature(diff)

                    geom_inter = road_geom.intersection(flood_geom)

                    if geom_inter.touches(geom_diff):
                        for part in geom_inter.asGeometryCollection():
                            polyline = part.asPolyline()
                            if len(polyline):
                                for point in [polyline[0], polyline[-1]]:
                                    point_geom = QgsGeometry.fromPoint(point)

                                    if point_geom.touches(geom_diff):
                                        exit_point = QgsFeature()
                                        exit_point.setGeometry(point_geom)
                                        exit_layer.addFeature(exit_point)

        del dry_roads_layer
        del exit_layer