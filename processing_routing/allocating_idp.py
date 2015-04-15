from qgis.utils import iface
from processing.core.GeoAlgorithm import GeoAlgorithm
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
import processing


class RoutableLayerGeoAlgorithm(GeoAlgorithm):

    ROADS = 'ROADS'
    IDP = 'IDP'
    EXIT = 'EXIT'
    OUTPUT_RESULT_LAYER = 'RESULT_LAYER'

    def defineCharacteristics(self):
        self.name = "Allocating IDP"
        self.group = "Routing"

        self.addParameter(ParameterVector(self.ROADS, 'Roads', [ParameterVector.VECTOR_TYPE_LINE], False))
        self.addParameter(ParameterVector(self.IDP, 'IDP', [ParameterVector.VECTOR_TYPE_POINT], False))
        self.addParameter(ParameterVector(self.EXIT, 'EXIT', [ParameterVector.VECTOR_TYPE_POINT], False))

        self.addOutput(OutputVector(self.OUTPUT_RESULT_LAYER, 'Result layer'))

    def processAlgorithm(self, progress):
        roads_layer = processing.getObject(roads_layer)
        idp_layer = processing.getObject(idp_layer)
        exit_layer = processing.getObject(exit_layer)

        final_layer = QgsVectorFileWriter(
            graph,
            None,
            roads_layer.dataProvider().fields(),
            QGis.WKBLineString,
            roads_layer.crs()
        )

        # prepare graph
        director = QgsLineVectorLayerDirector(roads_layer, -1, '', '', '', 3)
        properter = QgsDistanceArcProperter()
        director.addProperter(properter)
        crs = roads_layer.crs()
        builder = QgsGraphBuilder(crs)

        # prepare points
        idp = []
        for feature in processing.features(idp_layer):
          idp.append(feature.geometry().asPoint())

        tiedPoints = director.makeGraph(builder, idp)
        graph = builder.graph()

        all_result = {}

        for feature in processing.features(exit_layer):

            from_id = graph.findVertex(feature.geometry().asPoint())

            (tree, cost) = QgsGraphAnalyzer.dijkstra(graph, from_id, 0)

            result = {}

            for idp in processing.features(idp_layer):
                to_id = graph.findVertex(idp.geometry().asPoint())
                if cost[to_id] > 0:
                    result[idp.id()] = cost[to_id]
                    print tree
                    print cost

        print all_result
        del final_layer
