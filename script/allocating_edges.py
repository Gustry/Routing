from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException

layer_edge = QgsMapLayerRegistry.instance().mapLayersByName('edges3')[0]
layer_exit = QgsMapLayerRegistry.instance().mapLayersByName('cost_exits')[0]

tolerance =

for f in layer_edge.getFeatures():
    print f.geometry().asPolyline()