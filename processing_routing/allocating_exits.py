from qgis.utils import iface
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.parameters import ParameterVector, ParameterTableField, ParameterNumber
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
    CRITERION = 'CRITERION'
    FIELD = 'FIELD'
    EXITS = 'EXITS'
    IDP = 'IDP'
    OUTPUT_EXITS = 'EXITS_LAYER'

    def defineCharacteristics(self):
        self.name = "Allocating exits"
        self.group = "Routing"

        self.addParameter(ParameterVector(self.ROADS, 'Roads', [ParameterVector.VECTOR_TYPE_LINE], False))
        self.addParameter(ParameterNumber(self.CRITERION, 'Num criter', default=0))
        self.addParameter(ParameterTableField(self.FIELD, self.tr('Coef field'), self.ROADS, True))
        self.addParameter(ParameterVector(self.EXITS, 'Exits', [ParameterVector.VECTOR_TYPE_POINT], False))
        self.addParameter(ParameterVector(self.IDP, 'IDP', [ParameterVector.VECTOR_TYPE_POINT], False))

        self.addOutput(OutputVector(self.OUTPUT_EXITS, 'New exits'))

    def processAlgorithm(self, progress):
        roads_layer = self.getParameterValue(self.ROADS)
        roads_layer = getObjectFromUri(roads_layer)
        num_criter = self.getParameterValue(self.CRITERION)
        field = self.getParameterValue(self.FIELD)
        exits_layer = self.getParameterValue(self.EXITS)
        exits_layer = getObjectFromUri(exits_layer)
        idp_layer = self.getParameterValue(self.IDP)
        idp_layer = getObjectFromUri(idp_layer)

        output_exits = self.getOutputValue(self.OUTPUT_EXITS)

        tied_points = []
        for f in idp_layer.getFeatures():
            tied_points.append(f.geometry().asPoint())
        for f in exits_layer.getFeatures():
            tied_points.append(f.geometry().asPoint())

        graph = Graph(roads_layer, tied_points)
        layer = graph.cost_exits(idp_layer, exits_layer, num_criter)

        route_layer = QgsVectorFileWriter(
            output_exits,
            None,
            layer.dataProvider().fields(),
            QGis.WKBPoint,
            roads_layer.crs()
        )

        for feature in layer.getFeatures():
            route_layer.addFeature(feature)

        del route_layer