from Routing.core.graph import Graph
from qgis.utils import iface

layer = iface.activeLayer()
pt_start = QgsPoint(20.4529554239886, -34.0188548283715)
pt_end = QgsPoint(20.4359617949895, -34.0351452550364)
graph = Graph(layer, [])

print graph.cost_between(pt_start, pt_end)

