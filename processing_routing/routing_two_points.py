from qgis.utils import iface
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.parameters import ParameterVector, ParameterBoolean, ParameterTableField, ParameterNumber
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
    CRITERION = 'CRITERION'
    FIELD = 'FIELD'
    USE_TIED_POINTS = 'USE_TIED_POINTS'
    OUTPUT_ROUTE = 'ROUTE_LAYER'

    def defineCharacteristics(self):
        self.name = "Routing two points"
        self.group = "Routing"

        self.addParameter(ParameterVector(self.ROADS, 'Roads', [ParameterVector.VECTOR_TYPE_LINE], False))
        self.addParameter(ParameterNumber(self.CRITERION, 'Num criter', default=0))
        self.addParameter(ParameterTableField(self.FIELD, self.tr('Coef field'), self.ROADS, True))
        self.addParameter(ParameterVector(self.POINTS, 'Points (first 2 points)', [ParameterVector.VECTOR_TYPE_POINT], False))
        self.addParameter(ParameterBoolean(self.USE_TIED_POINTS, 'Use tied points', True))

        self.addOutput(OutputVector(self.OUTPUT_ROUTE, 'Route layer'))

    def processAlgorithm(self, progress):
        roads_layer = self.getParameterValue(self.ROADS)
        roads_layer = getObjectFromUri(roads_layer)
        points_layer = self.getParameterValue(self.POINTS)
        points_layer = getObjectFromUri(points_layer)
        use_tied_points = self.getParameterValue(self.USE_TIED_POINTS)
        num_criter = self.getParameterValue(self.CRITERION)
        field = self.getParameterValue(self.FIELD)
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

        features = points_layer.getFeatures()
        start_feature = features.next()
        end_feature = features.next()
        start = start_feature.geometry().asPoint()
        end = end_feature.geometry().asPoint()

        tied_points = []
        if use_tied_points:
            tied_points.append(start)
            tied_points.append(end)

        id_coef = roads_layer.fieldNameIndex(field)

        graph = Graph(roads_layer, tied_points, id_coef)
        layer = graph.route_between(start, end, num_criter)

        for feature in layer.getFeatures():
            route_layer.addFeature(feature)

        del route_layer