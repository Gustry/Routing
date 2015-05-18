# -*- coding: utf-8 -*-

from graph import Graph
from properter import MultiplyProperter

from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsPoint,
    QgsField,
    QgsFeatureRequest,
    QgsSpatialIndex
)

from PyQt4.QtCore import QVariant


class InasafeGraph(Graph):

    def __init__(
            self,
            layer,
            points=[],
            direction_field_id=-1,
            direct_direction_value='',
            reverse_direction_value='',
            both_direction_value='',
            default_direction=3,
            ctf_enabled=True,
            topology_tolerance=0,
            ellipsoid_id='WGS84',
            coefficient_field_id=None,
            name_coefficient_flood='flood'):

        Graph.__init__(
            self,
            layer,
            points,
            direction_field_id,
            direct_direction_value,
            reverse_direction_value,
            both_direction_value,
            default_direction,
            ctf_enabled,
            topology_tolerance,
            ellipsoid_id)

        if coefficient_field_id:
            self.add_cost(
                name_coefficient_flood,
                MultiplyProperter(coefficient_field_id, 1), True)

    def allocating_exits(self, idp_layer, exit_layer, cost_strategy='distance'):
        idp_exit_layer = QgsVectorLayer("Point", "Exits", "memory")
        idp_exit_layer.setCrs(self.crs)
        dp = idp_exit_layer.dataProvider()
        dp.addAttributes([
            QgsField("id_idp", QVariant.Int),
            QgsField("cost", QVariant.Double),
        ])
        idp_exit_layer.updateFields()

        route_layer = QgsVectorLayer("MultiLineString", "Route", "memory")
        route_layer.setCrs(self.crs)
        dp_route = route_layer.dataProvider()
        dp_route.addAttributes([
            QgsField("id_idp", QVariant.Int),
            QgsField("cost", QVariant.Double),
        ])
        route_layer.updateFields()

        # Working on exits
        for exit in exit_layer.getFeatures():
            idp_id = -1
            min_cost = -1
            for idp in idp_layer.getFeatures():
                cost = self.cost_between(
                    exit.geometry().asPoint(),
                    idp.geometry().asPoint(),
                    cost_strategy)

                if cost >= 0:
                    if cost < min_cost or min_cost <= 0:
                        min_cost = cost
                        idp_id = idp.id()

            if min_cost > 0:
                request = QgsFeatureRequest().setFilterFid(idp_id)
                idp = idp_layer.getFeatures(request).next()

                f = QgsFeature()
                attrs = [idp_id, min_cost]
                f.setAttributes(attrs)
                f.setGeometry(exit.geometry())
                dp.addFeatures([f])

                geom_route = self.route_between_geom(
                    idp.geometry().asPoint(),
                    exit.geometry().asPoint(),
                    cost_strategy)
                r_feature = QgsFeature()
                attrs = [idp_id, min_cost]
                r_feature.setGeometry(geom_route)
                r_feature.setAttributes(attrs)
                dp_route.addFeatures([r_feature])

        idp_exit_layer.updateExtents()
        route_layer.updateExtents()
        return idp_exit_layer, route_layer

    @staticmethod
    def _get_feature(layer, index, point):
        idx = index.nearestNeighbor(point, 1)[0]
        request = QgsFeatureRequest().setFilterFid(idx)
        return layer.getFeatures(request).next()

    def test_edges(self, exit_layer):

        cut = QgsVectorLayer("Point", "Exits", "memory")
        cut.setCrs(self.crs)
        dp = cut.dataProvider()

        route_layer = QgsVectorLayer("MultiLineString", "Route", "memory")
        route_layer.setCrs(self.crs)
        dp_route = route_layer.dataProvider()
        dp_route.addAttributes([
            QgsField("id_idp", QVariant.Int),
        ])
        route_layer.updateFields()

        index = QgsSpatialIndex()
        for exit in exit_layer.getFeatures():
            index.insertFeature(exit)

        index_idp_id = exit_layer.fieldNameIndex('idp_id')
        index_idp_id = 0

        for strongly_connected in self.tarjan():
            shift = strongly_connected[1:] + strongly_connected[:1]
            print strongly_connected
            for vertex_a, vertex_b in zip(strongly_connected, shift):
                feature_a = self._get_feature(exit_layer, index, self.get_vertex_point(vertex_a))
                print str(self.get_vertex_point(vertex_a)) + '<=>' + str(feature_a.geometry().asPoint()) + ' ' + str(feature_a.attributes())
                attributes_a = feature_a.attributes()
                feature_b = self._get_feature(exit_layer, index, self.get_vertex_point(vertex_b))
                attributes_b = feature_b.attributes()


                if attributes_a[index_idp_id] == attributes_b[index_idp_id]:
                    idp_id = attributes_a[index_idp_id]
                    print str(feature_a.geometry().asPoint()), str(feature_b.geometry().asPoint())
                    #self.show_route_between(feature_a.geometry().asPoint(), feature_b.geometry().asPoint())
                    geom = self.route_between_geom(feature_a.geometry().asPoint(), feature_b.geometry().asPoint())
                    route_feature = QgsFeature()
                    route_feature.setGeometry(geom)
                    route_feature.setAttributes([idp_id])
                    dp_route.addFeatures([route_feature])

        route_layer.updateExtents()
        cut.updateExtents()
        return route_layer, cut

    def allocating_edges_easy(self, new_exit_layer, edge_layer, cost_strategy='distance'):

        route_layer = QgsVectorLayer("MultiLineString", "Route", "memory")
        route_layer.setCrs(self.crs)
        dp_route = route_layer.dataProvider()
        dp_route.addAttributes([
            QgsField("id_idp", QVariant.Int),
            QgsField("cost", QVariant.Double),
        ])
        route_layer.updateFields()

        # Working on edges
        for edge in edge_layer.getFeatures():
            polyline = edge.geometry().asPolyline()
            print polyline
            points = [
                QgsPoint(polyline[0]),
                QgsPoint(polyline[-1])]

            point_start = None
            point_end = None
            for exit in new_exit_layer.getFeatures():
                point = exit.geometry().asPoint()
                if point == points[0]:
                    point_start = exit
                if point == points[1]:
                    point_end = exit
                # if point_start and point_end:
                #    break

            #print point_start
            #print point_end
            if not point_start or not point_end:
                dp_route.addFeatures([edge])
        route_layer.updateExtents()
        return route_layer
