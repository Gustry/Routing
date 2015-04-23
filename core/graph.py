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
    QgsSpatialIndex
)

from processing.core.GeoAlgorithmExecutionException import \
    GeoAlgorithmExecutionException


class Graph:

    def __init__(self, layer, points=[], topology_tolerance=0):
        self.layer = layer
        self.director = QgsLineVectorLayerDirector(layer, -1, '', '', '', 3)
        self.director.addProperter(QgsDistanceArcProperter())
        self.crs = self.layer.crs()
        self.builder = QgsGraphBuilder(self.crs, topologyTolerance=topology_tolerance)
        self.tiedPoint = self.director.makeGraph(self.builder, points)
        self.graph = self.builder.graph()
        self.dijkstra_results = {}
        self.vertices = QgsSpatialIndex()
        self.vertices_layer = QgsVectorLayer("Point", "Tied", "memory")
        self.vertices_layer_dp = self.vertices_layer.dataProvider()
        self._fill_layer()

    def _fill_layer(self):
        for vertex in self.get_id_vertices():
            self.vertices_layer_dp.addFeatures([
                self.get_vertex_feature(vertex)])

        self.vertices_layer_dp.updateExtents()

        for feature in self.vertices_layer.getFeatures():
            self.vertices.insertFeature(feature)

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

    def get_arc_count(self):
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
        return self.graph.arc(id_arc)

    def get_in_vertex_id(self, id_arc):
        return self.graph.arc(id_arc).inVertex()

    def get_out_vertex_id(self, id_arc):
        return self.graph.arc(id_arc).outVertex()

    def get_arc_line(self, id_arc):
        """Get the geometry of an arc according to an id.
        :return: The geometry.
        :rtype: QgsGeometry
        """
        arc = self.get_arc(id_arc)
        point_start = self.get_vertex_point(arc.inVertex())
        point_end = self.get_vertex_point(arc.outVertex())
        points = [point_start, point_end]
        return QgsGeometry.fromPolyline(points)

    def get_arc_feature(self, id_arc):
        """Get the feature of an arc according to an id.
        :return: The feature.
        :rtype: QgsFeature
        """
        feature = QgsFeature()
        geom = self.get_arc_line(id_arc)
        feature.setGeometry(geom)
        return feature

    def get_vertex_count(self):
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
        return self.graph.vertex(id_vertex)

    def get_vertex_point(self, id_vertex):
        """Get the point of a vertex according to an id.
        :return: The point.
        :rtype: QgsPoint
        """
        return self.get_vertex(id_vertex).point()

    def get_vertex_geom(self, id_vertex):
        """Get the geometry of a vertex according to an id.
        :return: The geometry.
        :rtype: QgsGeometry
        """
        return QgsGeometry.fromPoint(self.get_vertex_point(id_vertex))

    def get_vertex_feature(self, id_vertex):
        """Get the feature of a vertex according to an id.
        :return: The feature.
        :rtype: QgsFeature
        """
        feature = QgsFeature()
        geom = self.get_vertex_geom(id_vertex)
        feature.setGeometry(geom)
        return feature

    def get_nearest_vertex_id(self, point):
        """Get the nearest vertex id.
        :param point The point.
        :type point QgsPoint or int or QgsGraphVertex
        :return: The closest vertex id.
        :rtype: int
        """
        if isinstance(point, int):
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

    def dijkstra(self, start):
        """Compute dijkstra from a start point.
        :param start The start.
        :type start QgsPoint or int or QgsGraphVertex
        :return Dijkstra.
        :rtype tab
        """
        if start not in self.dijkstra_results.keys():
            vertex_id = self.get_nearest_vertex_id(start)
            results = QgsGraphAnalyzer.dijkstra(self.graph, vertex_id, 0)
            self.dijkstra_results[start] = results
        return self.dijkstra_results[start]

    def cost_between(self, start, end):
        """Compute cost between two points.
        :type start QgsPoint or int or QgsGraphVertex
        :type end QgsPoint or int or QgsGraphVertex
        :return The cost.
        :rtype int
        """
        vertex_start_id = self.get_nearest_vertex_id(start)
        vertex_stop_id = self.get_nearest_vertex_id(end)
        tree, cost = self.dijkstra(vertex_start_id)
        return tree[vertex_stop_id]

    def route_between(self, start, end):
        if self.cost_between(start, end) < 0:
            raise GeoAlgorithmExecutionException("Path not found")

        route_layer = QgsVectorLayer("LineString", "Line", "memory")
        data_provider = route_layer.dataProvider()

        tree, cost = self.dijkstra(start)
        vertex_start_id = self.get_nearest_vertex_id(start)
        vertex_stop_id = self.get_nearest_vertex_id(end)
        current_vertex = vertex_stop_id

        while current_vertex != vertex_start_id:
            arc_id = tree[current_vertex]
            feature = self.get_arc_feature(arc_id)
            data_provider.addFeatures([feature])
            current_vertex = self.get_out_vertex_id(arc_id)

        data_provider.updateExtents()
        return route_layer

    def route_info_between(self, start, end):
        return self.cost_between(start, end), self.route_between(start, end)

    def show_route_between(self, start, end):
        layer = self.route_between(start, end)
        QgsMapLayerRegistry.instance().addMapLayers([layer])

    def show_vertices(self):
        """DEBUG : show all vertices.
        """
        QgsMapLayerRegistry.instance().addMapLayers([self.vertices_layer])

    def show_arc(self):
        """DEBUG : show all arcs.
        """
        layer = QgsVectorLayer("LineString", "Lines", "memory")
        dp = layer.dataProvider()

        for edge_id in self.get_id_arcs():
            dp.addFeatures([self.get_arc_feature(edge_id)])

        dp.updateExtents()
        QgsMapLayerRegistry.instance().addMapLayers([layer])




    def cost_exits(self, idps, exits):

        exit_layer = QgsVectorLayer("Point?crs=epsg:4326&field=id_idp:integer&field=distance:integer", "Exits", "memory")
        pr_exit = exit_layer.dataProvider()

        for exit in exits.getFeatures():
            idp_id = -1
            min_cost = -1
            for idp in idps.getFeatures():
                cost = self.cost_between(idp.geometry().asPoint(), exit.geometry().asPoint())
                print "%s : %s ( %s ) -> %s" % (exit.id(), idp.id(), idp.geometry().asPoint(), cost)
                if cost >= 0:
                    if cost < min_cost or min_cost <= 0:
                        min_cost = cost
                        idp_id = idp.id()

                        #l = self.route_between(idp.geometry().asPoint(), exit.geometry().asPoint())
                        #QgsMapLayerRegistry.instance().addMapLayers([l])

            f = QgsFeature()
            attrs = [idp_id, min_cost]
            print attrs
            f.setAttributes(attrs)
            f.setGeometry(exit.geometry())
            pr_exit.addFeatures([f])

        pr_exit.updateExtents()
        return exit_layer