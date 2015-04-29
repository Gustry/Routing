# -*- coding: utf-8 -*-

from qgis.networkanalysis import (
    QgsLineVectorLayerDirector,
    QgsGraphVertex,
    QgsDistanceArcProperter,
    QgsGraphAnalyzer,
    QgsGraphBuilder
)

from qgis.core import (
    QgsVectorLayer,
    QgsGeometry,
    QgsFeature,
    QgsPoint,
    QgsMapLayerRegistry,
    QgsField,
    QgsFeatureRequest,
    QgsSpatialIndex
)

from PyQt4.QtCore import QVariant

from processing.core.GeoAlgorithmExecutionException import \
    GeoAlgorithmExecutionException

from properter import MultiplyProperter

class Graph:

    def __init__(self, layer, points=[], coef=None, topology_tolerance=0):
        self.layer = layer
        self.director = QgsLineVectorLayerDirector(layer, -1, '', '', '', 3)
        self.director.addProperter(QgsDistanceArcProperter())
        self.num_criterion = 1
        if coef:
            self.num_criterion += 1
            self.director.addProperter(MultiplyProperter(coef, 1))
        self.crs = self.layer.crs()
        self.builder = QgsGraphBuilder(self.crs, topologyTolerance=topology_tolerance)
        self.tiedPoint = self.director.makeGraph(self.builder, points)
        self.graph = self.builder.graph()
        self.dijkstra_results = {}

    '''
    ITERATOR
    '''
    def get_vertices(self):
        """Get a generator to loop over all vertices.

        :return: A list of vertices.
        :rtype: list
        """
        nb_vertices = self.graph.vertexCount()
        return (self.graph.vertex(i) for i in range(0, nb_vertices))

    def get_id_vertices(self):
        """Get a generator to loop over all vertices id.

        :return: A list of ids.
        :rtype: list
        """
        nb_vertices = self.graph.vertexCount()
        return xrange(0, nb_vertices)

    def get_arcs(self):
        """Get a generator to loop over all arcs.

        :return: A list of arcs.
        :rtype: list
        """
        nb_edges = self.graph.arcCount()
        return (self.graph.arc(i) for i in range(0, nb_edges))

    def get_id_arcs(self):
        """Get a generator to loop over all arcs id.

        :return: A list of ids.
        :rtype: list
        """
        nb_edges = self.graph.arcCount()
        return xrange(0, nb_edges)

    '''
    ARC
    '''
    def arc_count(self):
        """Get the number of arc.

        :return: The number of arc.
        :rtype: int
        """
        return self.graph.arcCount()

    def get_arc(self, id_arc):
        """Get an arc according to an id.

        :return: The arc.
        :rtype: QgsGraphArc
        """
        if id_arc < 0 or id_arc >= self.arc_count():
            msg = 'Arc %s doesn\'t exist' % id_arc
            raise GeoAlgorithmExecutionException(msg)

        return self.graph.arc(id_arc)

    def get_in_vertex_id(self, id_arc):
        return self.get_arc(id_arc).inVertex()

    def get_out_vertex_id(self, id_arc):
        return self.get_arc(id_arc).outVertex()

    def get_arc_linestring(self, id_arc):
        arc = self.get_arc(id_arc)
        point_start = self.get_vertex_point(arc.inVertex())
        point_end = self.get_vertex_point(arc.outVertex())
        linestring = [point_start, point_end]
        return linestring

    '''
    VERTEX
    '''
    def vertex_count(self):
        """Get the number of vertices.

        :return: The number of vertices.
        :rtype: int
        """
        return self.graph.vertexCount()

    def get_vertex(self, id_vertex):
        """Get a vertex according to an id.

        :return: The vertex.
        :rtype: QgsGraphVertex
        """
        if id_vertex < 0 or id_vertex >= self.vertex_count():
            msg = 'Vertex %s doesn\'t exist' % id_vertex
            raise GeoAlgorithmExecutionException(msg)

        return self.graph.vertex(id_vertex)

    def get_vertex_point(self, id_vertex):
        """Get the point of a vertex according to an id.

        :return: The point.
        :rtype: QgsPoint
        """
        return self.get_vertex(id_vertex).point()

    '''
    SEARCHING VERTEX
    '''
    def get_nearest_vertex_id(self, point):
        """Get the nearest vertex id.

        :param point The point.
        :type point QgsPoint or int or QgsGraphVertex.

        :return: The closest vertex id.
        :rtype: int
        """
        if isinstance(point, int):
            self.get_vertex(point)
            vertex_id = point

        elif isinstance(point, QgsGraphVertex):
            vertex_id = self.graph.findVertex(point.point())

        elif isinstance(point, QgsPoint):
            vertex_id = self.graph.findVertex(point)
            if vertex_id < 0:
                vertex = self.get_nearest_vertex(point)
                vertex_id = self.graph.findVertex(vertex.point())
        else:
            raise GeoAlgorithmExecutionException("unknown type")

        return vertex_id

    def get_nearest_vertex(self, point):
        """Get the nearest vertex.

        :param point The point.
        :type point QgsPoint

        :return The vertex.
        :rtype QgsGraphVertex
        """
        min = -1
        closest_vertex = None

        for vertex in self.get_vertices():
            dist = point.sqrDist(vertex.point())
            if dist < min or not closest_vertex:
                min = dist
                closest_vertex = vertex

        return closest_vertex

    '''
    ROUTING
    '''
    def dijkstra(self, start, criterion=0):
        """Compute dijkstra from a start point.

        :param start The start.
        :type start QgsPoint or int or QgsGraphVertex.

        :return Dijkstra : tree, cost
        :rtype: tab
        """

        if criterion >= self.num_criterion:
            msg = 'Property %s doesn\'t exist' % criterion
            raise GeoAlgorithmExecutionException(msg)

        if start not in self.dijkstra_results.keys():
            self.dijkstra_results[start] = {}

        if criterion not in self.dijkstra_results[start].keys():
            vertex_id = self.get_nearest_vertex_id(start)
            dijkstra = QgsGraphAnalyzer.dijkstra(
                self.graph, vertex_id, criterion)
            self.dijkstra_results[start][criterion] = dijkstra

        return self.dijkstra_results[start][criterion]

    def cost_between(self, start, end, criterion=0):
        """Compute cost between two points.

        :type start QgsPoint or int or QgsGraphVertex
        :type end QgsPoint or int or QgsGraphVertex
        
        :return The cost.
        :rtype int
        """
        vertex_start_id = self.get_nearest_vertex_id(start)
        vertex_stop_id = self.get_nearest_vertex_id(end)
        tree, cost = self.dijkstra(vertex_start_id, criterion)
        return cost[vertex_stop_id]

    def route_between_geom(self, start, end, criterion=0):
        cost = self.cost_between(start, end, criterion)
        if cost < 0:
            raise GeoAlgorithmExecutionException("Path not found")

        tree, cost = self.dijkstra(start, criterion)
        vertex_start_id = self.get_nearest_vertex_id(start)
        vertex_stop_id = self.get_nearest_vertex_id(end)
        current_vertex = vertex_stop_id

        multigeom = []
        while current_vertex != vertex_start_id:
            arc_id = tree[current_vertex]
            multigeom.append(self.get_arc_linestring(arc_id))
            current_vertex = self.get_out_vertex_id(arc_id)

        return QgsGeometry().fromMultiPolyline(multigeom)

    def route_between(self, start, end, criterion=0):
        geom = self.route_between_geom(start, end, criterion)
        return geom, geom.length(), self.cost_between(start, end, criterion)

    def show_route_between(self, start, end, criterion=0):
        route = self.route_between(start, end, criterion)
        geom = route[0]
        length = route[1]
        cost = route[2]

        route_layer = QgsVectorLayer("LineString", "Route %s" % cost, "memory")
        data_provider = route_layer.dataProvider()

        data_provider.addAttributes([
            QgsField("length", QVariant.Double),
            QgsField("cost", QVariant.Double)
        ])
        route_layer.updateFields()

        feature = QgsFeature()
        feature.setGeometry(geom)
        feature.setAttributes([length, cost])
        data_provider.addFeatures([feature])
        data_provider.updateExtents()
        QgsMapLayerRegistry.instance().addMapLayers([route_layer])

    def isochrone(self, start, cost, criterion=0):
        """Compute isochrone"""
        pass

    '''
    DEBUG
    '''
    def show_vertices(self):
        """DEBUG : show all vertices.
        """
        layer = QgsVectorLayer("Point", "Debug point", "memory")
        layer_dp = layer.dataProvider()

        layer_dp.addAttributes([
            QgsField("id_vertex", QVariant.Int),
            QgsField("in_arcs_nb", QVariant.Int),
            QgsField("out_arcs_nb", QVariant.Int),
            QgsField("arcs_nb", QVariant.Int)
        ])
        layer.updateFields()

        for id_vertex in self.get_id_vertices():
            vertex = self.get_vertex(id_vertex)

            feature = QgsFeature()
            geom = QgsGeometry.fromPoint(self.get_vertex_point(id_vertex))
            in_arcs_id = vertex.inArc()
            out_arcs_id = vertex.outArc()
            attrs = [
                id_vertex,
                len(in_arcs_id),
                len(out_arcs_id),
                len(in_arcs_id) + len(out_arcs_id)]
            feature.setAttributes(attrs)
            feature.setGeometry(geom)
            layer_dp.addFeatures([feature])
        layer.updateExtents()

        QgsMapLayerRegistry.instance().addMapLayers([layer])

    def show_arcs(self):
        """DEBUG : show all arcs.
        """
        layer = QgsVectorLayer("LineString", "Debug edges", "memory")
        dp = layer.dataProvider()
        attrs = []
        attrs.append(QgsField("id_arc", QVariant.Int))
        for i in range(0, self.num_criterion):
            attrs.append(QgsField("cost_%s" % i, QVariant.Double))
        attrs.append(QgsField("in_vertex", QVariant.Int))
        attrs.append(QgsField("out_vertex", QVariant.Int))

        dp.addAttributes(attrs)
        layer.updateFields()

        for arc_id in self.get_id_arcs():
            geom = QgsGeometry.fromPolyline(self.get_arc_linestring(arc_id))
            arc = self.get_arc(arc_id)
            out_vertex_id = self.get_out_vertex_id(arc_id)
            in_vertex_id = self.get_in_vertex_id(arc_id)

            attrs = []
            attrs.append(arc_id)
            attrs = attrs + arc.properties()
            attrs.append(in_vertex_id)
            attrs.append(out_vertex_id)

            feature = QgsFeature()
            feature.setAttributes(attrs)
            feature.setGeometry(geom)

            dp.addFeatures([feature])

        layer.updateExtents()
        QgsMapLayerRegistry.instance().addMapLayers([layer])

    '''
    SPECIFIC to InaSAFE
    '''
    def cost_exits(self, idp_layer, exit_layer, criterion=0):
        idp_exit_layer = QgsVectorLayer("Point", "Exits", "memory")
        dp = idp_exit_layer.dataProvider()
        dp.addAttributes([
            QgsField("id_idp", QVariant.Int),
            QgsField("cost", QVariant.Double),
        ])
        idp_exit_layer.updateFields()

        route_layer = QgsVectorLayer("MultiLineString", "Route", "memory")
        dp_route = route_layer.dataProvider()
        dp_route.addAttributes([
            QgsField("id_idp", QVariant.Int),
            QgsField("cost", QVariant.Double),
        ])
        route_layer.updateFields()

        for exit in exit_layer.getFeatures():
            idp_id = -1
            min_cost = -1
            for idp in idp_layer.getFeatures():
                cost = self.cost_between(
                    exit.geometry().asPoint(),
                    idp.geometry().asPoint(),
                    criterion)

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

                geom_route = self.route_between_multiline(idp.geometry().asPoint(), exit.geometry().asPoint(), criterion)
                r_feature = QgsFeature()
                attrs = [idp_id, min_cost]
                r_feature.setGeometry(geom_route)
                r_feature.setAttributes(attrs)
                dp_route.addFeatures([r_feature])

        idp_exit_layer.updateExtents()
        route_layer.updateExtents()
        return idp_exit_layer, route_layer