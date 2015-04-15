from qgis.utils import iface
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
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

from Routing.core.graph import Graph


class RoutingTwoPointsGeoAlgorithm(GeoAlgorithm):

    ROADS = 'ROADS'
    POINTS = 'POINTS'
    USE_TIED_POINTS = 'USE_TIED_POINTS'
    OUTPUT_ROUTE = 'ROUTE_LAYER'

    def defineCharacteristics(self):
        self.name = "Routing two points"
        self.group = "Routing"

        self.addParameter(ParameterVector(self.ROADS, 'Roads', [ParameterVector.VECTOR_TYPE_LINE], False))
        self.addParameter(ParameterVector(self.POINTS, 'Points', [ParameterVector.VECTOR_TYPE_POINT], False))
        self.addParameter(ParameterBoolean(self.USE_TIED_POINTS, 'Use tied points', True))

        self.addOutput(OutputVector(self.OUTPUT_ROUTE, 'Route layer'))

    def processAlgorithm(self, progress):
        roads_layer = self.getParameterValue(self.ROADS)
        roads_layer = getObjectFromUri(roads_layer)
        points_layer = self.getParameterValue(self.POINTS)
        points_layer = getObjectFromUri(points_layer)
        use_tied_points = self.getParameterValue(self.USE_TIED_POINTS)
        output_route = self.getOutputValue(self.OUTPUT_ROUTE)

        route_layer = QgsVectorFileWriter(
            output_route,
            None,
            roads_layer.dataProvider().fields(),
            QGis.WKBLineString,
            roads_layer.crs()
        )

        if points_layer.featureCount() < 2:
            raise GeoAlgorithmExecutionException("Not enough feature")

        start = points_layer.getFeatures().next().geometry().asPoint()
        end = points_layer.getFeatures().next().geometry().asPoint()

        tied_points = []
        if use_tied_points:
            tied_points.append(start)
            tied_points.append(end)

        graph = Graph(roads_layer, tied_points)
        layer = graph.route_between(start, end)

        for feature in layer.getFeatures():
            route_layer.writte(feature)

        del route_layer