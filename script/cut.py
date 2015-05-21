layer_edge = QgsMapLayerRegistry.instance().mapLayersByName('edges2')[0]
inGeom = QgsGeometry()

for f in layer_edge.getFeatures():
    inGeom = f.geometry()
    print inGeom.isMultipart()