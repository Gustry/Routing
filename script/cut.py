from processing.tools.vector import spatialindex, features

points = QgsMapLayerRegistry.instance().mapLayersByName('b')[0]
lines = QgsMapLayerRegistry.instance().mapLayersByName('a')[0]

idx_lines = spatialindex(lines)
lines_to_cut = []
for f in features(points):
    point = f.geometry().asPoint()
    results = idx_lines.nearestNeighbor(point, 1)
    lines_to_cut.append(QgsFeatureRequest().setFilterFid(results[0]))
    
print lines_to_cut

'''
for f in features(points):
    point = f.geometry().asPoint()
    results = idx_lines.nearestNeighbor(point, 1)
    request = QgsFeatureRequest().setFilterFid(results[0])
    line_feature = lines.getFeatures(request).next()
    geom = line_feature.geometry()
    r = geom.closestSegmentWithContext(point)
    new_point = r[1]
    index = r[2]
    polyline = geom.asPolyline()
    polyline.insert(index, new_point)
    print polyline[0:index+1]
    print polyline[-index-1:]
    
'''