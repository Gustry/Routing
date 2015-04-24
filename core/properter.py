from qgis.networkanalysis import QgsArcProperter
from unicodedata import numeric


class MultiplyProperter(QgsArcProperter):
    def __init__(self, attribute_id, default_value):
        QgsArcProperter.__init__(self)
        self.attribute_id = attribute_id
        self.DefaultValue = default_value

    def property(self, distance, feature):
        attrs = feature.attributes()
        val = distance * (numeric(attrs[self.attribute_id], 10) + 7)
        return val

    def requiredAttributes(self):
        l = []
        l.append(self.attribute_id)
        return l