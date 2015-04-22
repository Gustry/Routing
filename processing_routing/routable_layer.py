# -*- coding: utf-8 -*-

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterVector, ParameterBoolean
from processing.core.outputs import OutputVector
from processing.tools.dataobjects import getObjectFromUri

from qgis.core import QgsVectorFileWriter, QGis

from Routing.core.routable_layer import RoutableLayer


class RoutableLayerGeoAlgorithm(GeoAlgorithm):

    ROADS = 'ROADS'
    FLOOD = 'FLOOD'
    DELETE_RINGS = 'DELETE_RINGS'
    OUTPUT_ROUTABLE_LAYER = 'ROUTABLE_LAYER'
    OUTPUT_EXIT_LAYER = 'EXIT_LAYER'

    def defineCharacteristics(self):
        self.name = "Routable layer"
        self.group = "Routing"

        self.addParameter(ParameterVector(self.ROADS, 'Roads', [ParameterVector.VECTOR_TYPE_LINE], False))
        self.addParameter(ParameterVector(self.FLOOD, 'Flood', [ParameterVector.VECTOR_TYPE_POLYGON], False))

        self.addOutput(OutputVector(self.OUTPUT_ROUTABLE_LAYER, 'Routable layer'))
        self.addOutput(OutputVector(self.OUTPUT_EXIT_LAYER, 'Unroutable layer'))

    def processAlgorithm(self, progress):
        roads_parameter = self.getParameterValue(self.ROADS)
        roads_layer = getObjectFromUri(roads_parameter)
        flood_parameter = self.getParameterValue(self.FLOOD)
        flood_layer = getObjectFromUri(flood_parameter)
        output_routable_file = self.getOutputValue(self.OUTPUT_ROUTABLE_LAYER)
        output_exit_file = self.getOutputValue(self.OUTPUT_EXIT_LAYER)

        roads_writer = QgsVectorFileWriter(
            output_routable_file,
            None,
            roads_layer.dataProvider().fields(),
            QGis.WKBLineString,
            roads_layer.crs()
        )

        exit_writer = QgsVectorFileWriter(
            output_exit_file,
            None,
            roads_layer.dataProvider().fields(),
            QGis.WKBLineString,
            roads_layer.crs()
        )

        graph = RoutableLayer(roads_layer, flood_layer)
        exits_layer, routable_layer = graph.compute_without_index()

        if exits_layer.featureCount():
            for f in exits_layer.getFeatures():
                exit_writer.addFeature(f)

        if routable_layer.featureCount():
            for f in routable_layer.getFeatures():
                roads_writer.addFeature(f)

        del roads_writer
        del exit_writer