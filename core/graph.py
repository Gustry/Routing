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
            self.vertices_layer_dp.addFeatures([self.get_vertex_feature(vertex)])

        self.vertices_layer_dp.updateExtents()

        for feature in self.vertices_layer.getFeatures():
            self.vertices.insertFeature(feature)

    def get_vertices(self):
        nb_vertices = self.graph.vertexCount()
        return (self.graph.vertex(i) for i in range(0, nb_vertices))

    def get_id_vertices(self):
        nb_vertices = self.graph.vertexCount()
        return xrange(0, nb_vertices)

    def get_arcs(self):
        nb_edges = self.graph.arcCount()
        return (self.graph.arc(i) for i in range(0, nb_edges))

    def get_id_arcs(self):
        nb_edges = self.graph.arcCount()
        return xrange(0, nb_edges)

    def get_arc_count(self):
        return self.graph.arcCount()

    def get_arc(self, id_arc):
        return self.graph.arc(id_arc)

    def get_arc_line(self, id_arc):
        arc = self.get_arc(id_arc)
        point_start = self.get_vertex_point(arc.inVertex())
        point_end = self.get_vertex_point(arc.outVertex())
        points = [point_start, point_end]
        return QgsGeometry.fromPolyline(points)

    def get_arc_feature(self, id_arc):
        feature = QgsFeature()
        geom = self.get_arc_line(id_arc)
        feature.setGeometry(geom)
        return feature

    def get_vertex_count(self):
        return self.graph.vertexCount()

    def get_vertex(self, id_vertex):
        return self.graph.vertex(id_vertex)

    def get_vertex_point(self, id_vertex):
        return self.get_vertex(id_vertex).point()

    def get_vertex_geom(self, id_vertex):
        return QgsGeometry.fromPoint(self.get_vertex_point(id_vertex))

    def get_vertex_feature(self, id_vertex):
        feature = QgsFeature()
        geom = self.get_vertex_geom(id_vertex)
        feature.setGeometry(geom)
        return feature

    def get_nearest_vertex_id(self, point):
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
        min = -1
        closest_vertex = None

        for vertex in self.get_vertices():
            dist = point.sqrDist(vertex.point())
            if dist < min or not closest_vertex:
                min = dist
                closest_vertex = vertex

        return closest_vertex

    def dijkstra(self, start):
        if start not in self.dijkstra_results.keys():
            vertex_id = self.get_nearest_vertex_id(start)
            results = QgsGraphAnalyzer.dijkstra(self.graph, vertex_id, 0)
            self.dijkstra_results[start] = results
        return self.dijkstra_results[start]

    def cost_between(self, start, end):
        vertex_start_id = self.get_nearest_vertex_id(start)
        vertex_stop_id = self.get_nearest_vertex_id(end)
        tree, cost = self.dijkstra(vertex_start_id)
        return tree[vertex_stop_id]

    def show_vertices(self):
        QgsMapLayerRegistry.instance().addMapLayers([self.vertices_layer])

    def show_arc(self):
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

    def route_between(self, start, end):

        vertex_start_id = self.get_vertex(start)
        vertex_stop_id = self.get_vertex(end)
        tree, cost = self.compute_dijkstra(start)

        layer_way = QgsVectorLayer("LineString?crs=epsg:4326", "Line", "memory")
        pr_way = layer_way.dataProvider()

        if tree[vertex_stop_id] == -1:
            raise GeoAlgorithmExecutionException("Path not found")
            return layer_way

        current_vertex = vertex_stop_id

        while current_vertex != vertex_start_id:
            in_vertex_id = self.graph.arc(tree[current_vertex]).inVertex()
            out_vertex_id = self.graph.arc(tree[current_vertex]).outVertex()

            in_vertex = self.graph.vertex(in_vertex_id)
            out_vertex = self.graph.vertex(out_vertex_id)

            points = [in_vertex.point(), out_vertex.point()]

            fet = QgsFeature()
            fet.setGeometry(QgsGeometry.fromPolyline(points))
            pr_way.addFeatures([fet])

            current_vertex = out_vertex_id

        layer_way.updateExtents()
        return layer_way

    def show(self, point):

        nodes = QgsVectorLayer("Point", 'points', "memory")
        nodes_dp = nodes.dataProvider()

        f = QgsFeature()
        f.setGeometry(QgsGeometry.fromPoint(point))

        nearest = self.closest_vertex(point).point()
        f2 = QgsFeature()
        f2.setGeometry(QgsGeometry.fromPoint(nearest))

        nodes_dp.addFeatures([f, f2])
        nodes.updateExtents()

        QgsMapLayerRegistry.instance().addMapLayers([nodes])