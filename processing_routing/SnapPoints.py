# -*- coding: utf-8 -*-

from qgis.core import QGis, QgsFeature, QgsGeometry
from qgis.utils import iface
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterVector
from processing.core.outputs import OutputVector
from processing.tools.dataobjects import getObjectFromUri
from processing.tools import vector


class SnapPoints(GeoAlgorithm):

    POINTS = 'POINTS'
    OUTPUT = 'OUTPUT'

    def defineCharacteristics(self):
        self.name = "Snap points"
        self.group = "Vector creation tools"

        self.addParameter(ParameterVector(self.POINTS, 'Points', [ParameterVector.VECTOR_TYPE_POINT], False))

        self.addOutput(OutputVector(self.OUTPUT, 'Output'))

    def processAlgorithm(self, progress):
        points_layer = self.getParameterValue(self.POINTS)
        points_layer = getObjectFromUri(points_layer)

        writer = self.getOutputFromName(self.OUTPUT).getVectorWriter(
            points_layer.dataProvider().fields(),
            QGis.WKBPoint,
            points_layer.crs())

        snapper = iface.mapCanvas().snappingUtils()

        for feature in vector.features(points_layer):
            result = snapper.snapToMap(feature.geometry().asPoint())
            if result.type() == 2:
                f = QgsFeature()
                f.setAttributes(feature.attributes())
                f.setGeometry(QgsGeometry.fromPoint(result.point()))
                writer.addFeature(f)

        del writer
