from Routing.core.graph import Graph, InasafeGraph
from Routing.core.properter import MultiplyProperter
layer_routable = QgsMapLayerRegistry.instance().mapLayersByName('routable_layer')[0]
coef = layer_routable.fieldNameIndex('multiply')
layer_idp = QgsMapLayerRegistry.instance().mapLayersByName('idp')[0]
layer_exit = QgsMapLayerRegistry.instance().mapLayersByName('exit_layer')[0]
g = InasafeGraph(layer_routable, [], 0, coef)
p1 = QgsPoint(20.4529554239886, -34.0188548283715)
p2 = QgsPoint(20.4359617949895, -34.0351452550364)

g.show_route_between(p1,p2,'flood')
layers = g.cost_exits(layer_idp,layer_exit,'distance')
QgsMapLayerRegistry.instance().addMapLayers(layers)