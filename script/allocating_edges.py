from Routing.core.inasafe_graph import InasafeGraph
from processing.core.GeoAlgorithmExecutionException import \
    GeoAlgorithmExecutionException

layer_edge = QgsMapLayerRegistry.instance().mapLayersByName('edges')[0]
layer_exit = QgsMapLayerRegistry.instance().mapLayersByName('cost_exits')[0]

tied_points = [ f.geometry().asPoint() for f in layer_exit.getFeatures()]
g = InasafeGraph(layer_edge, tied_points)

layers = g.test_edges(layer_exit)
QgsMapLayerRegistry.instance().addMapLayers(layers)