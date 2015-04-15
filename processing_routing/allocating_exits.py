from qgis.utils import iface
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.parameters import ParameterVector
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


class AllocatingExitsGeoAlgorithm(GeoAlgorithm):

    ROADS = 'ROADS'
    POINTS = 'POINTS'
    OUTPUT_EXITS = 'EXITS_LAYER'

    def defineCharacteristics(self):
        self.name = "Allocating exits"
        self.group = "Routing"

        self.addParameter(ParameterVector(self.ROADS, 'Roads', [ParameterVector.VECTOR_TYPE_LINE], False))
        self.addParameter(ParameterVector(self.POINTS, 'Exits', [ParameterVector.VECTOR_TYPE_POINT], False))

        self.addOutput(OutputVector(self.OUTPUT_EXITS, 'New exits'))

    def processAlgorithm(self, progress):
        roads_layer = self.getParameterValue(self.ROADS)
        roads_layer = getObjectFromUri(roads_layer)
        points_layer = self.getParameterValue(self.POINTS)
        points_layer = getObjectFromUri(points_layer)
        output_route = self.getOutputValue(self.OUTPUT_ROUTE)

        route_layer = QgsVectorFileWriter(
            output_route,
            None,
            roads_layer.dataProvider().fields(),
            QGis.WKBLineString,
            roads_layer.crs()
        )

        if points_layer.featureCount() < 2:
            raise GeoAlgorithmExecutionException("Not enough feature, minimum 2")

        start = points_layer.getFeatures().next().geometry().asPoint()
        end = points_layer.getFeatures().next().geometry().asPoint()
        graph = Graph(roads_layer, [start, end])
        #graph.compute_route(start, end)

        del route_layer