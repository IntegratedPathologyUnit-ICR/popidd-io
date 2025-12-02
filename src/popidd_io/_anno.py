import pathlib

import geopandas
import numpy
import pandas
from napari.types import FullLayerData
from shapely import MultiPolygon, Polygon

# Add here the geojson  and parquet reading and writing support for qupath compatibility
# geojson to shapes and shapes to geojson
# parquet to shapes for cell annotations


def shape2feat(layer: FullLayerData) -> dict | None:
    if len(layer[0]) == 1:
        if "qupath_comp" in layer[1]:
            shape = numpy.dot(
                layer[0][0], [[0, 1], [1, 0]]
            )  # QUpath rotates and flips images.
        else:
            shape = layer[0][0]
        feat_geom = Polygon(shape)
    elif len(layer[0]) > 1:
        geoms = []
        for shape in layer[0]:
            if "qupath_comp" in layer[1]:
                shape = numpy.dot(
                    shape, [[0, 1], [1, 0]]
                )  # QUpath rotates and flips images.
            geoms.append(Polygon(shape))
        feat_geom = MultiPolygon(geoms)
    else:
        print("WARNING: This shape layer is empty!")
        return None
    feature = {
        "type": "Feature",
        "properties": {"objectType": "annotation", "name": layer[1]["name"]},
        "geometry": feat_geom.__geo_interface__,
    }

    return feature


def point2feat(layer: FullLayerData) -> dict:
    raise NotImplementedError
    return {}


# GeoJSON#


def load_geojson(path: str | pathlib.Path) -> list[FullLayerData]:
    """
    Load a GeoJSON file and convert it to a list of shape layers.

    Parameters:
    path (str | pathlib.Path): The path to the GeoJSON file.

    Returns:
    list[FullLayerData]: A list of FullLayerData containing the shape layer information.
    """

    if isinstance(path, str):
        path = pathlib.Path(path)

    geo_anno = geopandas.read_file(path)
    # Need to grab additional feature properties and save them as shape layer metadata
    napari_layers = []
    # Split off code below to its own function(s?) -> parse geopandas file and 1)populate annotation list, 2) generate shape_layer_data entry (or similar, need to check latest napari devs)

    for anno in geo_anno.itertuples():
        if anno.name is None:
            try:
                if isinstance(anno.classification, dict):
                    name = anno.classification["name"]
                else:  # Older versions load the dict as a string
                    import ast

                    name = ast.literal_eval(anno.classification)["name"]
            except (AttributeError, KeyError, ValueError):
                name = anno.Index
        else:
            name = anno.name

        if "Polygon" in anno.geometry.geom_type:
            anno_layer = []
            if anno.geometry.geom_type == "Polygon":
                coordinates = anno.geometry.exterior.coords[:]
                anno_layer.append(coordinates)
            elif anno.geometry.geom_type == "MultiPolygon":
                for poly in anno.geometry.geoms:
                    coordinates = poly.exterior.coords[:]
                    anno_layer.append(coordinates)
            else:
                raise NotImplementedError(anno.geometry.geom_type)
            napari_layers.append(
                (
                    anno_layer,
                    {
                        "name": f"Annot. {name}",
                        "shape_type": "polygon",
                        "rotate": -90,
                        "scale": [
                            -1,
                            1,
                        ],  # Needs to be set to img layer scale, with *-1,*1
                        "blending": "translucent",
                        "edge_color": "#55007fff",
                        "edge_width": 60,
                        "face_color": "transparent",
                        "text": {
                            "string": name,
                            "size": 12,
                            "scaling": True,
                            "anchor": "upper_left",
                            "color": "#550000ff",
                        },
                        "metadata": {"qupath_comp": True},
                    },
                    "shapes",
                )
            )
        elif "Point" in anno.geometry.geom_type:
            anno_layer = []
            if anno.geometry.geom_type == "Point":
                coordinates = anno.geometry.coords[0]
                anno_layer.append(coordinates)
            elif anno.geometry.geom_type == "MultiPoint":
                for point in anno.geometry.geoms:
                    coordinates = point.coords[0]
                    anno_layer.append(coordinates)
            else:
                raise NotImplementedError(anno.geometry.geom_type)
            napari_layers.append(
                (
                    anno_layer,
                    {
                        "name": f"Annot. {name}",
                        "rotate": -90,
                        "scale": [
                            -1,
                            1,
                        ],  # Needs to be set to img layer scale, with *-1,*1
                        "text": {
                            "string": name,
                            "size": 12,
                            "scaling": True,
                            "anchor": "upper_left",
                            "color": "#550000ff",
                        },
                        "metadata": {"qupath_comp": True},
                    },
                    "points",
                )
            )
        else:
            print(f"{anno.geometry.geom_type} are not supported!")

    return napari_layers


def write_geojson(out_path: str | pathlib.Path, features: dict) -> list[str]:
    gdf = geopandas.GeoDataFrame.from_features(features)
    # gdf.to_file(filename= pathlib.Path(out_path) / f"anno_{"-".join(saved_annotations)}.geojson", driver="GeoJSON")
    gdf.to_file(filename=f"{pathlib.Path(out_path)}.geojson", driver="GeoJSON")
    return [str(out_path)]


# Parquet#


def load_parquet(path: str | pathlib.Path) -> list[FullLayerData]:
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
