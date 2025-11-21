# For now I will only add here support for geojson and parquet writing of shapes/points/labels layers

import pathlib

from napari.types import FullLayerData

from ._anno import point2feat, shape2feat, write_geojson


def save_manyannolayers(
    out_path: str | pathlib.Path, layers: list[FullLayerData]
) -> list[str]:
    feature_list = []
    saved_annotations = []
    for layer_data_tuple in layers:
        if layer_data_tuple[2] == "shapes":
            print("Shape layer")
            feature = shape2feat(layer_data_tuple)
            saved_annotations.append(layer_data_tuple[1]["name"])
            feature_list.append(feature)
        elif layer_data_tuple[2] == "points":
            print("Points layer")
            feature = point2feat(layer_data_tuple)
            saved_annotations.append(layer_data_tuple[1]["name"])
            feature_list.append(feature)
        else:
            print("This layer type IS NOT supported!")

    annotations = {
        "type": "FeatureCollection",
        "features": feature_list,
        "properties": {"shape_layers": saved_annotations, "prop2": "val2"},
    }

    write_geojson(out_path, annotations)

    return [str(out_path)]


# def save_geojson(out_path: str | pathlib.Path, shapes: list[FullLayerData]) -> list[str]:

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
