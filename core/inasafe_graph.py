# -*- coding: utf-8 -*-

from graph import Graph
from properter import MultiplyProperter

from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsField,
    QgsFeatureRequest
)

from PyQt4.QtCore import QVariant


class InasafeGraph(Graph):
    """Manage a InaSAFE graph."""

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

        """Constructor for the InaSAFE graph.

        :param layer: The road layer.
        :type layer: QgsVectorLayer

        :param points: The list of points to add as tied points.
        :type points: list

        :param direction_field_id: Field containing road direction value.
        :type direction_field_id: int

        :param direct_direction_value: Value for one-way road.
        :type direct_direction_value: str

        :param reverse_direction_value: Value for reverse one-way road.
        :type reverse_direction_value: str

        :param both_direction_value: Value for road.
        :type both_direction_value: str

        :param default_direction: Default direction value (1: direct direction,
            2: reverse direction, 3: both direction)
        :type default_direction: int

        :param ctf_enabled: Enable coordinate transform from source graph.
        :type ctf_enabled: bool

        :param topology_tolerance: Tolerance between two source points.
        :type topology_tolerance: float

        :param ellipsoid_id: Ellipsoid for edge measurement. Default WGS84.
        :type ellipsoid_id: str

        :param coefficient_field_id: Field containing the coefficient.
        :type coefficient_field_id: int

        :param name_coefficient_flood: Name the cost strategy.
        :type name_coefficient_flood: str
        """

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

    def allocating_exits(
            self, idp_layer, exit_layer, cost_strategy='distance'):
        """Assign an IDP to each exit.

        :param idp_layer: The IDP layer.
        :type idp_layer: QgsVectorLayer

        :param exit_layer: The exit layer.
        :type exit_layer: QgsVectorLayer

        :param cost_strategy: The cost strategy to use.
        :type cost_strategy: str

        :return: Two vector layers : the exit layer and the route layer.
        :rtype: list
        """
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

        for one_exit in exit_layer.getFeatures():
            idp_id = -1
            min_cost = -1
            for idp in idp_layer.getFeatures():
                cost = self.cost_between(
                    one_exit.geometry().asPoint(),
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
                attributes = [idp_id, min_cost]
                f.setAttributes(attributes)
                f.setGeometry(one_exit.geometry())
                dp.addFeatures([f])

                geom_route = self.route_between_geom(
                    idp.geometry().asPoint(),
                    one_exit.geometry().asPoint(),
                    cost_strategy)
                r_feature = QgsFeature()
                attributes = [idp_id, min_cost]
                r_feature.setGeometry(geom_route)
                r_feature.setAttributes(attributes)
                dp_route.addFeatures([r_feature])

        idp_exit_layer.updateExtents()
        route_layer.updateExtents()
        return idp_exit_layer, route_layer
