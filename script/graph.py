from Routing.core.graph import Graph, InasafeGraph
from Routing.core.properter import MultiplyProperter


layer_routable = QgsMapLayerRegistry.instance().mapLayersByName('routable_layer')[0]
coef = layer_routable.fieldNameIndex('multiply')
layer_idp = QgsMapLayerRegistry.instance().mapLayersByName('idp')[0]
layer_exit = QgsMapLayerRegistry.instance().mapLayersByName('exit_layer')[0]
#layer_edge = QgsMapLayerRegistry.instance().mapLayersByName('Edge')[0]

g = InasafeGraph(layer_routable, [], coefficient_field_id=coef)

'''
p1 = QgsPoint(20.4529554239886, -34.0188548283715)
p2 = QgsPoint(20.4359617949895, -34.0351452550364)

#g.show_route_between(p1,p2,'flood')
#layers = g.allocating_exits(layer_idp,layer_exit, 'flood')
#QgsMapLayerRegistry.instance().addMapLayers(layers)
'''
layer_exit = QgsMapLayerRegistry.instance().mapLayersByName('extract')[0]
layer_edge = QgsMapLayerRegistry.instance().mapLayersByName('extract2')[0]
layers = g.allocating_edges_easy(layer_exit, layer_edge)
QgsMapLayerRegistry.instance().addMapLayers([layers])