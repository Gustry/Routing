# -*- coding: utf-8 -*-

from qgis.networkanalysis import (
    QgsLineVectorLayerDirector,
    QgsDistanceArcProperter,
    QgsGraphAnalyzer,
    QgsGraphBuilder)

from qgis.core import (
    QgsVectorLayer, QgsGeometry, QgsFeature, QgsPoint, QgsMapLayerRegistry)

class Graph:

    def __init__(self, layer, points=[]):

        self.points = points
        self.layer = layer
        self.director = QgsLineVectorLayerDirector(layer, -1, '', '', '', 3)
        self.director.addProperter(QgsDistanceArcProperter())
        self.crs = self.layer.crs()
        self.builder = QgsGraphBuilder(self.crs, topologyTolerance=0)

        self.tiedPoint = self.director.makeGraph(self.builder, self.points)
        self.graph = self.builder.graph()
        self.dijkstra_results = {}

    def compute_dijkstra(self, start):

        if start not in self.dijkstra_results.keys():

            vertex_start_id = self.get_vertex(start)

            results = QgsGraphAnalyzer.dijkstra(self.graph, vertex_start_id, 0)
            self.dijkstra_results[start] = results

        return self.dijkstra_results[start]

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

    def cost_between(self, start, end):

        vertex_start_id = self.get_vertex(start)
        vertex_stop_id = self.get_vertex(end)
        tree, cost = self.compute_dijkstra(start)
        return tree[vertex_stop_id]

    def route_between(self, start, end):

        vertex_start_id = self.get_vertex(start)
        vertex_stop_id = self.get_vertex(end)
        tree, cost = self.compute_dijkstra(start)

        layer_way = QgsVectorLayer("LineString?crs=epsg:4326", "Line", "memory")
        pr_way = layer_way.dataProvider()

        if tree[vertex_stop_id] == -1:
            print "Path not found"
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

    def get_vertex(self, point):
        vertex_id = self.graph.findVertex(point)
        if vertex_id < 0:
            vertex = self.closest_vertex(point)
            vertex_id = self.graph.findVertex(vertex.point())
        return vertex_id

    def closest_vertex(self, point):
        min = -1
        closest_vertex = None

        vertices = [self.graph.vertex(i) for i in range(0, self.graph.vertexCount())]
        for vertex in vertices:
            dist = point.sqrDist(vertex.point())
            if dist < min or not closest_vertex:
                min = dist
                closest_vertex = vertex

        return closest_vertex

    def show_all(self):

        nodes = QgsVectorLayer("Point", 'points', "memory")
        nodes_dp = nodes.dataProvider()

        vertices = [self.graph.vertex(i) for i in range(0, self.graph.vertexCount())]
        for vertex in vertices:
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPoint(vertex.point()))
            nodes_dp.addFeatures([f])

        nodes.updateExtents()
        QgsMapLayerRegistry.instance().addMapLayers([nodes])

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