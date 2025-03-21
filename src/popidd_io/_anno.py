import pathlib

import geopandas
import numpy
import pandas
from napari.types import LayerDataTuple
from shapely import MultiPolygon, Polygon

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
        path = pathlib.Path(path)

    geo_anno = geopandas.read_file(path) # Need to grab additional feature properties and save them as shape layer metadata
    shape_layer_data = []
    for anno, _ in enumerate(geo_anno["name"]):
        print(anno, _)
        nap_anno = []
        if geo_anno["geometry"][anno].geom_type == "Polygon":
            nap_anno.append(geo_anno["geometry"][anno].exterior.coords[:])
        elif geo_anno["geometry"][anno].geom_type == "MultiPolygon":
            for poly in geo_anno["geometry"][anno].geoms:
                nap_anno.append(poly.exterior.coords[:])
        else:
            print(geo_anno["geometry"][anno].geom_type)
            raise NotImplementedError(geo_anno["geometry"][anno].geom_type)

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
                    "metadata": {"qupath_comp": True},
                },
                "shapes",
            )
        )
    return shape_layer_data

#Need to split off writer code and add relevant widget
def save_geojson(out_path: str | pathlib.Path, shapes: list[LayerDataTuple]) -> list[str]:
        saved_annotations = []
        features = []
        for layer in shapes:
            print(len(layer))
            print(type(layer))
            print(layer[0])
            print(layer[1]["name"])
            print(layer[1].keys())
            print(layer[2])
            if len(layer[0]) == 1:
                if "qupath_comp" in layer[1]:
                    shape = numpy.dot(layer[0][0], [[0, 1], [1, 0]]) # QUpath rotates and flips images.
                else:
                    shape = layer[0][0]
                feat_geom = Polygon(shape)
            elif len(layer[0]) > 1:
                geoms = []
                for shape in layer[0]:
                    if "qupath_comp" in layer[1]:
                        shape = numpy.dot(shape, [[0, 1], [1, 0]]) # QUpath rotates and flips images.
                    geoms.append(Polygon(shape))
                feat_geom = MultiPolygon(geoms)
            else:
                print("WARNING: This shape layer is empty!")
                continue
            feature = {
                "type": "Feature",
                "properties": {
                    "objectType":"annotation",
                    "name":layer[1]["name"]},
                    "geometry": feat_geom.__geo_interface__
            }
            features.append(feature)
            saved_annotations.append(layer[1]["name"])
        feature_collection = {
            "type":"FeatureCollection",
            "features": features,
            "properties": {
                "shape_layers": saved_annotations,
                "prop2": "val2"
            }
        }
        print(saved_annotations)
        print(out_path)
        print(f"anno_{"-".join(saved_annotations)}.geojson")
        gdf = geopandas.GeoDataFrame.from_features(feature_collection)
        # gdf.to_file(filename= pathlib.Path(out_path) / f"anno_{"-".join(saved_annotations)}.geojson", driver="GeoJSON")
        gdf.to_file(filename= f"{pathlib.Path(out_path)}.geojson", driver="GeoJSON")

        return [out_path]

    # def save_geojson(shapes: list[LayerDataTuple], img: LayerDataTuple, outDir: pathlib.Path):
    #         features = []
    #         for layer in shapes:
    #             if len(layer.data) == 1:
    #                 if layer.metadata.get("qupath_comp"):
    #                     shape = numpy.dot(layer.data[0], [[0, 1], [1, 0]]) # QUpath rotates and flips images.
    #                 else:
    #                     shape = layer.data[0]
    #                 feat_geom = Polygon(shape)
    #             elif len(layer.data) > 1:
    #                 geoms = []
    #                 for shape in layer.data:
    #                     if layer.metadata.get("qupath_comp"):
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
    #                     "name":layer.name},
    #                     "geometry": feat_geom.__geo_interface__
    #             }
    #             features.append(feature)
    #         feature_collection = {
    #             "type":"FeatureCollection",
    #             "features": features,
    #             "properties": {
    #                 "prop1": "val1",
    #                 "prop2": "val2"
    #             }
    #         }
    #         gdf = geopandas.GeoDataFrame.from_features(feature_collection)
    #         gdf.to_file(filename= outDir / f"{img[1]["name"]}.geojson", driver="GeoJSON")

def load_parquet(path: str | pathlib.Path) -> list[LayerDataTuple]:
    """
    Load a Parquet file and return its contents as a list of LayerDataTuple.
    Parameters:
    path (str | pathlib.Path): The path to the Parquet file.
    Returns:
    list[LayerDataTuple]: A list containing the data from the Parquet file,
        formatted as a LayerDataTuple with the data as a NumPy array,
        an empty dictionary for metadata, and the string "labels".
    """
    print("WIP function")
    if isinstance(path, str):
        print("PATH IS A STRINGG!!!!!")
        path = pathlib.Path(path)

    df = pandas.read_parquet(path)
    print("Experiental")
    print(df)

    return [(df.to_numpy(), {}, "labels")]
