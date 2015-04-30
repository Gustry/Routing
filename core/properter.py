from qgis.networkanalysis import QgsArcProperter


class MultiplyProperter(QgsArcProperter):
    def __init__(self, attribute_id, default_value):
        QgsArcProperter.__init__(self)
        self.attribute_id = attribute_id
        self.DefaultValue = default_value

    def property(self, distance, feature):
        attrs = feature.attributes()
        val = distance * float(attrs[self.attribute_id])

        if val < 0:
            return 10000
        return val

    def requiredAttributes(self):
        l = []
        l.append(self.attribute_id)
        return l