from PyQt4.QtCore import QVariant
from qgis.networkanalysis import QgsArcProperter


class SpeedProperter(QgsArcProperter):
    def __init__(self, attribute_id, default_value, to_metric_factor = 1000 ):
        QgsArcProperter.__init__(self)
        self.AttributeId = attribute_id
        self.DefaultValue = default_value
        self.ToMetricFactor = to_metric_factor

    def property(self, distance, feature):
        map = feature.attributeMap()
        it = map[self.AttributeId]

        val = distance / (it.toDouble()[0] * self.ToMetricFactor)

        if val <= 0.0:
            return QVariant(distance / (self.DefaultValue * self.ToMetricFactor))

        return QVariant(val)

    def requiredAttributes(self):
        l = []
        l.append(self.AttributeId)
        return l