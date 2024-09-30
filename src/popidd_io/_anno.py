import pathlib

import geopandas
import pandas
from napari.types import LayerDataTuple

# Add here the geojson  and parquet reading and writing support for qupath compatibility

# geojson to shapes and shapes to geojson

# parquet to shapes for cell annotations


def load_geojson(path: str | pathlib.Path) -> list[LayerDataTuple]:
    """
    Load a GeoJSON file and convert it to a list of shape layers.

    Parameters:
    path (str | pathlib.Path): The path to the GeoJSON file.

    Returns:
    list[LayerDataTuple]: A list of LayerDataTuple containing the shape layer information.
    """

    if isinstance(path, str):
        print("PATH IS A STRINGG!!!!!")
        path = pathlib.Path(path)

    geo_anno = geopandas.read_file(path)
    shape_layer_data = []
    for anno, _ in enumerate(geo_anno["name"]):
        print(anno, _)
        nap_anno = []
        if geo_anno["geometry"][anno].type == "Polygon":
            nap_anno.append(geo_anno["geometry"][anno].exterior.coords[:])
        elif geo_anno["geometry"][anno].type == "MultiPolygon":
            for poly in geo_anno["geometry"][anno].geoms:
                nap_anno.append(poly.exterior.coords[:])
        else:
            print(geo_anno["geometry"][anno].type)
            raise NotImplementedError(print(geo_anno["geometry"][anno].type))

        shape_layer_data.append(
            (
                nap_anno,
                {
                    "name": _,
                    "shape_type": "polygon",
                    "rotate": -90,
                    "scale": [
                        -1,
                        1,
                    ],  # Needs to be set to img layer scale, with *-1,*1
                    "metadata": {"from_geoJSON": True},
                },
                "shapes",
            )
        )
    return shape_layer_data


def load_parquet(path: str | pathlib.Path) -> list[LayerDataTuple]:

    if isinstance(path, str):
        print("PATH IS A STRINGG!!!!!")
        path = pathlib.Path(path)

    df = pandas.read_parquet(path)
    print("Experiental")
    print(df)


# def save_geojson

# def wAnno(
#         viewer: "napari.Viewer",
#         imgAnno: "napari.layers.Image",
#         shapeAnno: "napari.layers.Shapes",
#         annoDir = pathlib.Path("")
#         ):

#     features = []
#     for layer in shapeAnno:
#         geoms = []
#         for shape in layer.data:
#             if layer.metadata.get("nap_generated"):
#                 shape = numpy.dot(shape, [[0, 1], [1, 0]]) # QUpath rotates and flips images. WIP to make it standard for our workflow too
#             geoms.append(Polygon(shape))
#         mpoly = MultiPolygon(geoms)
#         feature = {
#             "type": "Feature",
#             "properties": {
#                 "objectType":"annotation",
#                 "name":layer.name},
#                 "geometry": mpoly.__geo_interface__
#         }
#         features.append(feature)
#     feature_collection = {
#         "type":"FeatureCollection",
#         "features": features
#     }

#     gdf = geopandas.GeoDataFrame.from_features(feature_collection)
#     gdf.to_file(filename= annoDir / f"{imgAnno.name}.geojson", driver="GeoJSON")

# def save_parquet():
