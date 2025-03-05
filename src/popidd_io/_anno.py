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
        path = pathlib.Path(path)

    geo_anno = geopandas.read_file(path)
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
                    "metadata": {"from_geoJSON": True},
                },
                "shapes",
            )
        )
    return shape_layer_data


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


# def save_geojson
