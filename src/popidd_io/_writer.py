# For now I will only add here support for geojson and parquet writing of shapes/points/labels layers

# from ._anno import


# def save_geojson(out_path: str | pathlib.Path, shapes: list[LayerDataTuple]) -> list[str]:

#         saved_annotations = []
#         features = []
#         for layer in shapes:
#             print(len(layer))
#             print(type(layer))
#             print(layer[0])
#             print(layer[1]["name"])
#             print(layer[1].keys())
#             print(layer[2])
#             if len(layer[0]) == 1:
#                 if "qupath_comp" in layer[1].keys():
#                     shape = numpy.dot(layer[0][0], [[0, 1], [1, 0]]) # QUpath rotates and flips images.
#                 else:
#                     shape = layer[0][0]
#                 feat_geom = Polygon(shape)
#             elif len(layer[0]) > 1:
#                 geoms = []
#                 for shape in layer[0]:
#                     if "qupath_comp" in layer[1].keys():
#                         shape = numpy.dot(shape, [[0, 1], [1, 0]]) # QUpath rotates and flips images.
#                     geoms.append(Polygon(shape))
#                 feat_geom = MultiPolygon(geoms)
#             else:
#                 print("WARNING: This shape layer is empty!")
#                 continue
#             feature = {
#                 "type": "Feature",
#                 "properties": {
#                     "objectType":"annotation",
#                     "name":layer[1]["name"]},
#                     "geometry": feat_geom.__geo_interface__
#             }
#             features.append(feature)
#             saved_annotations.append(layer[1]["name"])
#         feature_collection = {
#             "type":"FeatureCollection",
#             "features": features,
#             "properties": {
#                 "shape_layers": saved_annotations,
#                 "prop2": "val2"
#             }
#         }
#         print(saved_annotations)
#         print(out_path)
#         print(f"anno_{"-".join(saved_annotations)}.geojson")
#         gdf = geopandas.GeoDataFrame.from_features(feature_collection)
#         # gdf.to_file(filename= pathlib.Path(out_path) / f"anno_{"-".join(saved_annotations)}.geojson", driver="GeoJSON")
#         gdf.to_file(filename= f"{pathlib.Path(out_path)}.geojson", driver="GeoJSON")

#         return [out_path]
