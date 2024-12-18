import pytest

from popidd_io import get_anno_reader, get_image_reader

# make_napari_viewer is a pytest fixture that returns a napari viewer object
# you don't need to import it, as long as napari is installed
# in your testing environment

# tmp_path is a pytest fixture

# def test_image_reader(tmp_path):
#     """An example of how you might test your plugin."""

#     # write some fake data using your supported file format
#     my_test_file = str(tmp_path / "myfile.npy")
#     original_data = np.random.rand(20, 20)
#     np.save(my_test_file, original_data)

#     # try to read it back in
#     reader = napari_get_reader(my_test_file)
#     assert callable(reader)

#     # make sure we're delivering the right format
#     layer_data_list = reader(my_test_file)
#     assert isinstance(layer_data_list, list) and len(layer_data_list) > 0
#     layer_data_tuple = layer_data_list[0]
#     assert isinstance(layer_data_tuple, tuple) and len(layer_data_tuple) > 0

#     # make sure it's the same as it started
#     np.testing.assert_allclose(original_data, layer_data_tuple[0])


# def test_get_reader_pass():
#     reader = napari_get_reader("fake.file")
#     assert reader is None


# Add here pass and fail tests for the readers
@pytest.fixture
def write_im2file(tmp_path):
    def write_tiff(file):
        import numpy
        from tifffile import TiffWriter

        # TIff generation snippet from tiffile
        data = numpy.random.randint(0, 255, (8, 2, 512, 512, 3), "uint8")
        subresolutions = 2
        pixelsize = 0.29  # micrometer
        tiff_file = f"{tmp_path}/{file}"
        with TiffWriter(tiff_file, bigtiff=True) as tif:
            metadata = {
                "axes": "TCYXS",
                "SignificantBits": 8,
                "TimeIncrement": 0.1,
                "TimeIncrementUnit": "s",
                "PhysicalSizeX": pixelsize,
                "PhysicalSizeXUnit": "µm",
                "PhysicalSizeY": pixelsize,
                "PhysicalSizeYUnit": "µm",
                "Channel": {"Name": ["Channel 1", "Channel 2"]},
                "Plane": {
                    "PositionX": [0.0] * 16,
                    "PositionXUnit": ["µm"] * 16,
                },
                "Description": "A multi-dimensional, multi-resolution image",
                "MapAnnotation": {  # for OMERO
                    "Namespace": "openmicroscopy.org/PyramidResolution",
                    "1": "256 256",
                    "2": "128 128",
                },
            }
            options = dict(
                photometric="rgb",
                tile=(128, 128),
                compression="jpeg",
                resolutionunit="CENTIMETER",
                maxworkers=2,
            )
            tif.write(
                data,
                subifds=subresolutions,
                resolution=(1e4 / pixelsize, 1e4 / pixelsize),
                metadata=metadata,
                **options,
            )
            # write pyramid levels to the two subifds
            # in production use resampling to generate sub-resolution images
            for level in range(subresolutions):
                mag = 2 ** (level + 1)
                tif.write(
                    data[..., ::mag, ::mag, :],
                    subfiletype=1,
                    resolution=(1e4 / mag / pixelsize, 1e4 / mag / pixelsize),
                    **options,
                )
            # add a thumbnail image as a separate series
            # it is recognized by QuPath as an associated image
            thumbnail = (data[0, 0, ::8, ::8] >> 2).astype("uint8")
            tif.write(thumbnail, metadata={"Name": "thumbnail"})

        return data, tiff_file

    return write_tiff


def test_img_reader_pass():
    reader = get_image_reader("fake.file")
    assert reader is None


def test_img_reader_list(write_im2file):
    _, path1 = write_im2file("temp1.ome.tif")
    _, path2 = write_im2file("temp2.ome.tif")
    reader = get_image_reader([path1, path2])
    assert callable(reader)


def test_img_reader(write_im2file):
    data, test_file = write_im2file("temp.ome.tif")
    reader = get_image_reader(test_file)
    assert callable(reader)

    layer_data_list = reader(test_file)
    assert isinstance(layer_data_list, list) and len(layer_data_list) > 0
    assert (
        isinstance(layer_data_list[0], tuple) and len(layer_data_list[0]) > 0
    )
    assert data.shape == layer_data_list[0][0][0].shape
    # numpy.testing.assert_allclose(data, layer_data_list[0][0][0].compute()) #Numpy of 1st lvl of dask array list


def test_anno_reader_pass():
    reader = get_anno_reader("fake.file")
    assert reader is None
