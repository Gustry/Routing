from qgis.core import QgsSnappingUtils
snapper = QgsSnappingUtils()

layer_edge = QgsMapLayerRegistry.instance().mapLayersByName('edges')[0]
snapping_type = QgsSnapper.SnapToSegment
tolerance = 1
unit = QgsTolerance.LayerUnits
layer_config = QgsSnappingUtils.LayerConfig(layer_edge, snapping_type, tolerance, unit)
snapper.setLayers([layer_config])
snap_mode = QgsSnappingUtils.SnapAdvanced
snapper.setSnapToMapMode(snap_mode)

p1 = QgsPoint(20.4529554239886, -34.0188548283715)
r = snapper.snapToMap(p1)
print r.type()

#snapper=QgsSnapper(iface.mapCanvas().mapSettings())
#snapper = setSnapMode