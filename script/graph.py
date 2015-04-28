from Routing.core.graph import Graph
from qgis.utils import iface

#iface.activeLayer()

layer_routable = QgsMapLayerRegistry.instance().mapLayersByName('routable_layer')[0]
layer_idp = QgsMapLayerRegistry.instance().mapLayersByName('idp')[0]
layer_exit = QgsMapLayerRegistry.instance().mapLayersByName('exit_layer')[0]
pt_start = QgsPoint(20.4529554239886, -34.0188548283715)
pt_end = QgsPoint(20.4359617949895, -34.0351452550364)
id_coef = layer_routable.fieldNameIndex('multiply')
g = Graph(layer_routable, [], id_coef)
# g.show_vertices()
layers = g.cost_exits(layer_idp,layer_exit,1)
QgsMapLayerRegistry.instance().addMapLayers(layers)