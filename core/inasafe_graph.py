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
            points=None,
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
        srs = self.crs.toWkt()
        idp_exit_layer = QgsVectorLayer(
            'Point?crs=' + srs, 'Exits', 'memory')
        dp = idp_exit_layer.dataProvider()
        dp.addAttributes([
            QgsField('id_idp', QVariant.Int),
            QgsField('cost', QVariant.Double),
        ])
        idp_exit_layer.updateFields()

        route_layer = QgsVectorLayer(
            'MultiLineString?crs=' + srs, 'Route', 'memory')
        dp_route = route_layer.dataProvider()
        dp_route.addAttributes([
            QgsField('id_idp', QVariant.Int),
            QgsField('cost', QVariant.Double),
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
