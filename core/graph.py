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
    QgsField
)

from PyQt4.QtCore import QVariant

from processing.core.GeoAlgorithmExecutionException import \
    GeoAlgorithmExecutionException


class Graph(object):

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
            topology_tolerance=0.0,
            ellipsoid_id='WGS84'):

        self.dijkstra_results = {}
        self.properties = []
        self.layer = layer
        self.points = points
        self.topology_tolerance = topology_tolerance
        self.crs = self.layer.crs()
        self.ctf_enabled = ctf_enabled
        self.ellipsoid_id = ellipsoid_id
        self.director = QgsLineVectorLayerDirector(
            layer,
            direction_field_id,
            direct_direction_value,
            reverse_direction_value,
            both_direction_value,
            default_direction)
        self.add_cost('distance', QgsDistanceArcProperter())
        self.builder = None
        self.tiedPoint = None
        self.graph = None
        self.build()

    '''
    BUILDER
    '''
    def build(self):
        self.builder = QgsGraphBuilder(
            self.crs,
            otfEnabled=self.ctf_enabled,
            topologyTolerance=self.topology_tolerance,
            ellipsoidID=self.ellipsoid_id)
        self.tiedPoint = self.director.makeGraph(self.builder, self.points)
        self.distance_area = self.builder.distanceArea()
        self.graph = self.builder.graph()

    def add_cost(self, name, cost_stategy, build=False):
        if name not in self.properties:
            self.director.addProperter(cost_stategy)
            self.properties.append(name)

            if build:
                self.build()

            return True
        else:
            return False

    '''
    ITERATOR
    '''
    def get_vertices(self):
        """Get a generator to loop over all vertices.

        :return: A list of vertices.
        :rtype: list
        """
        nb_vertices = self.graph.vertexCount()
        return (self.graph.vertex(i) for i in xrange(0, nb_vertices))

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
        return (self.graph.arc(i) for i in xrange(0, nb_edges))

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

    def get_neighbours_out(self, id_vertex):
        vertex = self.get_vertex(id_vertex)
        vertices = []
        for id_arc in vertex.outArc():
            vertices.append(self.get_in_vertex_id(id_arc))
        return vertices

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
        minimum = -1
        closest_vertex = None

        for vertex in self.get_vertices():
            dist = point.sqrDist(vertex.point())
            if dist < minimum or not closest_vertex:
                minimum = dist
                closest_vertex = vertex

        return closest_vertex

    '''
    ROUTING
    '''
    def dijkstra(self, start, cost_strategy='distance'):
        """Compute dijkstra from a start point.

        :param start The start.
        :type start QgsPoint or int or QgsGraphVertex.

        :return Dijkstra : tree, cost
        :rtype: tab
        """

        if cost_strategy not in self.properties:
            msg = 'Cost %s doesn\'t exist' % cost_strategy
            raise GeoAlgorithmExecutionException(msg)

        if start not in self.dijkstra_results.keys():
            self.dijkstra_results[start] = {}

        if cost_strategy not in self.dijkstra_results[start].keys():
            vertex_id = self.get_nearest_vertex_id(start)
            criterion = self.properties.index(cost_strategy)
            dijkstra = QgsGraphAnalyzer.dijkstra(
                self.graph, vertex_id, criterion)

            self.dijkstra_results[start][cost_strategy] = dijkstra

        return self.dijkstra_results[start][cost_strategy]

    def cost_between(self, start, end, cost_strategy='distance'):
        """Compute cost between two points.

        :type start QgsPoint or int or QgsGraphVertex
        :type end QgsPoint or int or QgsGraphVertex

        :return The cost.
        :rtype int
        """
        vertex_start_id = self.get_nearest_vertex_id(start)
        vertex_stop_id = self.get_nearest_vertex_id(end)
        tree, cost = self.dijkstra(vertex_start_id, cost_strategy)
        cost = cost[vertex_stop_id]
        if cost == 'inf':
            cost = -1
        return cost

    def route_between_geom(self, start, end, cost_strategy='distance'):
        cost = self.cost_between(start, end, cost_strategy)
        if cost < 0:
            raise GeoAlgorithmExecutionException("Path not found")

        tree, cost = self.dijkstra(start, cost_strategy)
        vertex_start_id = self.get_nearest_vertex_id(start)
        vertex_stop_id = self.get_nearest_vertex_id(end)
        current_vertex = vertex_stop_id

        multigeom = []
        while current_vertex != vertex_start_id:
            arc_id = tree[current_vertex]
            multigeom.append(self.get_arc_linestring(arc_id))
            current_vertex = self.get_out_vertex_id(arc_id)

        return QgsGeometry().fromMultiPolyline(multigeom)

    def route_between(self, start, end, cost_strategy='distance'):
        geom = self.route_between_geom(start, end, cost_strategy)
        return \
            geom, geom.length(), self.cost_between(start, end, cost_strategy)

    def show_route_between(self, start, end, cost_strategy='distance'):
        route = self.route_between(start, end, cost_strategy)
        geom = route[0]
        length = route[1]
        cost = route[2]

        route_layer = QgsVectorLayer("LineString", "Route %s" % cost, "memory")
        route_layer.setCrs(self.crs)
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

    def isochrone(self, start, cost, cost_strategy='distance'):
        """Compute isochrone"""
        return None

    '''
    ANALYSE
    '''

    def tarjan(self):
        class StrongCC(object):

            def strong_connect(self, head):
                lowlink, count, stack = self.lowlink, self.count, self.stack
                lowlink[head] = count[head] = self.counter = self.counter + 1
                stack.append(head)

                for tail in self.graph.get_neighbours_out(head):
                    if tail not in count:
                        self.strong_connect(tail)
                        lowlink[head] = min(lowlink[head], lowlink[tail])
                    elif count[tail] < count[head]:
                        if tail in self.stack:
                            lowlink[head] = min(lowlink[head], count[tail])

                if lowlink[head] == count[head]:
                    component = []
                    while stack and count[stack[-1]] >= count[head]:
                        component.append(stack.pop())
                    self.connected_components.append(component)

            def __call__(self, graph):
                self.graph = graph
                self.counter = 0
                self.count = {}
                self.lowlink = {}
                self.stack = []
                self.connected_components = []

                for id_vertex in self.graph.get_id_vertices():
                    if id_vertex not in self.count:
                        self.strong_connect(id_vertex)

                return self.connected_components

        strongly_connected_components = StrongCC()
        return strongly_connected_components(self)

    def dfs(self, vertex_id, visited=None):

        if visited is None:
            visited = []

        visited.append(vertex_id)
        for next_vertex in self.get_neighbours_out(vertex_id):
            if next_vertex not in visited:
                self.dfs(next_vertex, visited)
        return visited

    '''
    DEBUG
    '''
    def show_vertices(self):
        """DEBUG : show all vertices.
        """
        layer = QgsVectorLayer("Point?crs", "Debug point", "memory")
        layer.setCrs(self.crs)
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
        layer.setCrs(self.crs)
        dp = layer.dataProvider()
        attrs = []
        attrs.append(QgsField("id_arc", QVariant.Int))
        for i, strategy in enumerate(self.properties):
            attrs.append(QgsField("%s_%s" % (i, strategy), QVariant.Double))
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