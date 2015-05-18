from Routing.core.inasafe_graph import InasafeGraph
from processing.core.GeoAlgorithmExecutionException import \
    GeoAlgorithmExecutionException

layer_edge = QgsMapLayerRegistry.instance().mapLayersByName('edges')[0]
layer_exit = QgsMapLayerRegistry.instance().mapLayersByName('cost_exits')[0]

tied_points = [ f.geometry().asPoint() for f in layer_exit.getFeatures()]
g = InasafeGraph(layer_edge, tied_points,topology_tolerance=0.00001,ctf_enabled=False)
g.show_vertices()
#layers = g.test(layer_exit, 'id_idp')
# QgsMapLayerRegistry.instance().addMapLayers(layers)