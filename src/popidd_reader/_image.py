import pathlib, tifffile, zarr, numpy,warnings

from typing import Optional
from napari.types import LayerDataTuple
from napari.utils.notifications import WarningNotification
from napari.utils import Colormap
from xml.etree import ElementTree

from dask import array as darray


def read_img(img, load_mem): #img is pathlib path
    # Loading Image data
    image = tifffile.imread(img, aszarr=True)
    image = zarr.open(image, "r") 
    if isinstance(image, zarr.hierarchy.Group):
        zarray = [array for _, array in image.arrays()]
    else:
        zarray = [image]
    
    print(len(zarray), zarray[0], zarray[0].shape)

    dask_array = darray.from_zarr(zarray[-1])  # Convert zarr array to Dask array
    max_val, mean_val = darray.compute(dask_array.max(), dask_array.mean())
    #need to add here test for image modality
    print(dask_array.shape, dask_array)
    print(mean_val)
    modality = "BF"
    if mean_val < 100:
        modality = "IF"
    if 1 < max_val <= 255: #Image in 8bit col
        print("8bit!")
        int_scale = 255
    elif 255 < max_val <= 4095: # Image is 12bit colour, not 16! -> Checking actual values since Bits entry in XML lies and says 12bits for the Luca 8bit image
        print("12bit!")
        int_scale = 4095
        # int_scale = 255
    elif 4095 < max_val <= 65535: # image in 16bit colour
        print("16 bit!")
        int_scale = 65535
        # int_scale = 255
    else:
        raise NotImplementedError

    del dask_array
    if not load_mem:
        zarray = [darray.from_zarr(array) for array in zarray]

    return zarray, int_scale, modality # returns list of zarr arrays

def _get_mdIF(TiffFile):
    new_format = False
    fluor_to_marker = False
    xml = ElementTree.fromstring(TiffFile.series[0].pages[0].tags["ImageDescription"].value)
    if xml.find(".//LibraryAsJSON") is not None:
        import json
        dicti = json.loads(xml.find(".//LibraryAsJSON").text)
        if "spectra" in dicti.keys():
            new_format = True
            fluor_to_marker = {item["fluor"]: item["marker"] for item in dicti["spectra"] if "fluor" in item and "marker" in item}

    colmap_channels = {}
    for page in TiffFile.series[0].pages:
        xml = ElementTree.fromstring(page.tags["ImageDescription"].value)
        # tree = ElementTree.ElementTree(xml)
        # filename = f"page_{str(page)}_xml.xml"
        # tree.write(filename, encoding='utf-8', xml_declaration=True)
        if new_format == True:
            colmap_channels[
                xml.find(".//Responsivity/Band/Name").text
                ] = tuple(float(x) for x in xml.find(".//Color").text.split(","))
        else:
            colmap_channels[
                xml.find(".//Responsivity/Filter/Name").text
                ] = tuple(float(x) for x in xml.find(".//Color").text.split(","))

    print(colmap_channels)
    colmap_channels = {key: tuple(
            v/255 if max(colmap_channels[key]) > 1 else v for v in val
        ) for key, val in colmap_channels.items()} 
    print(colmap_channels)
    return fluor_to_marker, colmap_channels, new_format

def read_md(img, modality):
    # Loading Image metadata
    res_scale = (1,1)
    with tifffile.TiffFile(img) as src:
        full_res_tags = {
            tag.name: tag.value for tag in src.series[0].pages[0].tags.values() 
            if tag.name not in [
                "StripOffsets", "StripByteCounts", "TileOffsets", 
                "TileByteCounts"] 
            and not isinstance(tag.value, numpy.ndarray)
        }
        full_res_tags["ImagePath"] = img
        try:
            if str(full_res_tags["ResolutionUnit"]) == "RESUNIT.CENTIMETER":
                xres = full_res_tags["XResolution"]
                yres = full_res_tags["YResolution"]
                x_scale = xres[1] / xres[0]
                y_scale = yres[1] / yres[0]
                res_scale = (x_scale, y_scale)
            else:
                raise NotImplementedError("Scaling supports only images in centimeters")
        except Exception as e:
            warning_noMD = warnings.warn(f"Could not detect resolution metadata for image \n {img.stem}. \n Exception: {e}")
            WarningNotification(warning_noMD)

        md = full_res_tags
        md["path"] = img
        md["modality"] = modality
        md["res_scale"] = res_scale

        if modality == "IF":
            md["fluor_to_marker"], md["colmap_channels"], md["new_format"] = _get_mdIF(src)
    
    return md


def load_img(
    path: str | pathlib.Path, modality: Optional[str] = None, load_mem: bool = False 
    ) -> list[LayerDataTuple]:

    if isinstance(path, str):
        print("PATH IS A STRINGG!!!!!")
        path = pathlib.Path(path)

    zarray, int_scale, _ = read_img(path, load_mem)
    if modality is None:
        modality = _
    md = read_md(path, modality)
    md["int_scale"] = int_scale

    print("Image was initiliased")

    if modality=="BF":
        print("Brightfield")
        img_layer_data = [(
            zarray,
            {"name":path.stem, "scale":md["res_scale"], 
            "metadata":md, "contrast_limits":[0, md["int_scale"]]},
            "image")]
    else:
        print("Fluorescence")
        img_layer_data = []
        for index, (target, col) in enumerate(md["colmap_channels"].items()):
            md["dye"] = target
            layer = md["dye"]
            if md["new_format"] == True:
                md["biomarker"] = md["fluor_to_marker"][target]
                layer = md["biomarker"]
            cmap = Colormap(
                colors=numpy.array([(0, 0, 0, 1), col + (1,)]), name=target)
            
            channel_zarray = [array[index, :, :] for array in zarray]

            img_layer_data.append((
                channel_zarray,
                {"name":f"{layer}_{path.stem}",
                "scale":md["res_scale"], "colormap":cmap, "blending":"additive",
                "metadata":md, "contrast_limits":[0, md["int_scale"]]},
                "image"
            ))

    return img_layer_data


def image_reader(
    viewer: "napari.Viewer",
    bf_imgs = pathlib.Path(""),
    if_imgs = pathlib.Path(""),
    load_mem = bool
    ):
    
    empty_flag = True

    for img in bf_imgs:
        if img.is_file():

            # Loading Image data
            image = tifffile.imread(img, aszarr=True)
            image = zarr.open(image, "r") 
            if isinstance(image, zarr.hierarchy.Group):
                zarray = [array for _, array in image.arrays()]
            else:
                zarray = [image]
            
            print(type(zarray[0]), zarray[0], zarray[0].shape)

            # Loading Image metadata
            res_scale = (1,1)
            with tifffile.TiffFile(img) as src:
                full_res_tags = {
                    tag.name: tag.value for tag in src.series[0].pages[0].tags.values() 
                    if tag.name not in [
                        "StripOffsets", "StripByteCounts", "TileOffsets", 
                        "TileByteCounts"] 
                    and not isinstance(tag.value, numpy.ndarray)
                }

                try:
                    if str(full_res_tags["ResolutionUnit"]) == "RESUNIT.CENTIMETER":
                        xres = full_res_tags["XResolution"]
                        yres = full_res_tags["YResolution"]
                        x_scale = xres[1] / xres[0]
                        y_scale = yres[1] / yres[0]
                        res_scale = (x_scale, y_scale)
                    else:
                        raise NotImplementedError("Scaling supports only images in centimeters")
                except Exception as e:
                    warning_noMD = warnings.warn(f"Could not detect resolution metadata for image: \n {img.stem}. \n Exception: {e}")
                    WarningNotification(warning_noMD)

            dask_array = darray.from_zarr(zarray[-1])  # Convert zarr array to Dask array
            max_val = darray.compute(dask_array.max())[0]
            del dask_array
            if 1 < max_val <= 255: #Image in 8bit col
                int_scale = 255
            elif 255 < max_val <= 4095: # Image is 12bit colour, not 16! -> Checking actual values since Bits entry in XML lies and says 12bits for the Luca 8bit image
                int_scale = 4095
            elif 4095 < max_val <= 65535:
                int_scale = 65535
            else:
                raise NotImplementedError

            md = full_res_tags
            md["path"] = img
            md["int_scale"] = int_scale

            # Adding Image to viewer
            viewer.add_image(
                zarray, name=img.stem, 
                scale=res_scale, 
                metadata=full_res_tags, contrast_limits=[0, int_scale])

            empty_flag = False
    
    for img in if_imgs:
        if img.is_file():

            # Loading Image data
            image = tifffile.imread(img, aszarr=True)
            image = zarr.open(image, "r") 
            if isinstance(image, zarr.hierarchy.Group):
                zarray = [array for _, array in image.arrays()]
            else:
                zarray = [image]
            
            print(len(zarray), zarray[0], zarray[0].shape)

            # Loading Image metadata
            res_scale = (1,1)
            with tifffile.TiffFile(img) as src:
                full_res_tags = {
                    tag.name: tag.value for tag in src.series[0].pages[0].tags.values() 
                    if tag.name not in [
                        "StripOffsets", "StripByteCounts", "TileOffsets", 
                        "TileByteCounts"] 
                    and not isinstance(tag.value, numpy.ndarray)
                }
                full_res_tags["ImagePath"] = img
                try:
                    if str(full_res_tags["ResolutionUnit"]) == "RESUNIT.CENTIMETER":
                        xres = full_res_tags["XResolution"]
                        yres = full_res_tags["YResolution"]
                        x_scale = xres[1] / xres[0]
                        y_scale = yres[1] / yres[0]
                        scale = (x_scale, y_scale)
                    else:
                        raise NotImplementedError("Scaling supports only images in centimeters")
                except Exception as e:
                    warning_noMD = warnings.warn(f"Could not detect resolution metadata for image \n {img.stem}. \n Exception: {e}")
                    WarningNotification(warning_noMD)

                new_format = False
                xml = ElementTree.fromstring(src.series[0].pages[0].tags["ImageDescription"].value)
                if xml.find(".//LibraryAsJSON") is not None:
                    import json
                    dicti = json.loads(xml.find(".//LibraryAsJSON").text)
                    if "spectra" in dicti.keys():
                        new_format = True
                        fluor_to_marker = {item["fluor"]: item["marker"] for item in dicti["spectra"] if "fluor" in item and "marker" in item}

                colmap_channels = {}
                for page in src.series[0].pages:
                    xml = ElementTree.fromstring(page.tags["ImageDescription"].value)
                    # tree = ElementTree.ElementTree(xml)
                    # filename = f"page_{str(page)}_xml.xml"
                    # tree.write(filename, encoding='utf-8', xml_declaration=True)
                    if new_format == True:
                        colmap_channels[
                            xml.find(".//Responsivity/Band/Name").text
                            ] = tuple(float(x) for x in xml.find(".//Color").text.split(","))
                    else:
                        colmap_channels[
                            xml.find(".//Responsivity/Filter/Name").text
                            ] = tuple(float(x) for x in xml.find(".//Color").text.split(","))

                colmap_channels = {key: tuple(
                        v/255 if max(colmap_channels[key]) > 1 else v for v in val
                    ) for key, val in colmap_channels.items()} 

            dask_array = darray.from_zarr(zarray[-1])  # Convert zarr array to Dask array
            max_val = darray.compute(dask_array.max())[0]
            del dask_array
            if 1 < max_val <= 255: #Image in 8bit col
                int_scale = 255
            elif 255 < max_val <= 4095: # Image is 12bit colour, not 16! -> Checking actual values since Bits entry in XML lies and says 12bits for the Luca 8bit image
                int_scale = 4095
            elif 4095 < max_val <= 65535:
                int_scale = 65535
            else:
                raise NotImplementedError

            if not load_mem:
                zarray = [darray.from_zarr(array) for array in zarray]

            for index, (target, col) in enumerate(colmap_channels.items()):
                md = full_res_tags
                md["dye"] = target
                layer = md["dye"]
                md["path"] = img
                md["int_scale"] = int_scale
                if new_format == True:
                    md["biomarker"] = fluor_to_marker[target]
                    layer = md["biomarker"]

                cmap = Colormap(
                    colors=numpy.array([(0, 0, 0, 1), col + (1,)]),
                    name=target)

                channel_zarray = [array[index, :, :] for array in zarray]

                viewer.add_image(
                    channel_zarray, name=f"{layer}_{img.stem}", 
                    scale=scale, colormap=cmap, blending="additive", 
                    metadata=md, contrast_limits=[0, int_scale])

            empty_flag = False

    if empty_flag == True: # Should the selection be empty it will return a warning on the GUI
        warning_empty = warnings.warn("No image(s) selected for loading.")
        WarningNotification(warning_empty)

# def image_reader(
#     viewer: "napari.Viewer",
#     bf_imgs = pathlib.Path(""),
#     if_imgs = pathlib.Path(""),
#     load_mem = bool
#     ):
    
#     empty_flag = True

#     for img in bf_imgs:
#         if img.is_file():

#             # Loading Image data
#             image = tifffile.imread(img, aszarr=True)
#             image = zarr.open(image, "r") 
#             if isinstance(image, zarr.hierarchy.Group):
#                 zarray = [array for _, array in image.arrays()]
#             else:
#                 zarray = [image]
            
#             print(type(zarray[0]), zarray[0], zarray[0].shape)

#             # Loading Image metadata
#             res_scale = (1,1)
#             with tifffile.TiffFile(img) as src:
#                 full_res_tags = {
#                     tag.name: tag.value for tag in src.series[0].pages[0].tags.values() 
#                     if tag.name not in [
#                         "StripOffsets", "StripByteCounts", "TileOffsets", 
#                         "TileByteCounts"] 
#                     and not isinstance(tag.value, numpy.ndarray)
#                 }

#                 try:
#                     if str(full_res_tags["ResolutionUnit"]) == "RESUNIT.CENTIMETER":
#                         xres = full_res_tags["XResolution"]
#                         yres = full_res_tags["YResolution"]
#                         x_scale = xres[1] / xres[0]
#                         y_scale = yres[1] / yres[0]
#                         res_scale = (x_scale, y_scale)
#                     else:
#                         raise NotImplementedError("Scaling supports only images in centimeters")
#                 except Exception as e:
#                     warning_noMD = warnings.warn(f"Could not detect resolution metadata for image: \n {img.stem}. \n Exception: {e}")
#                     WarningNotification(warning_noMD)

#             dask_array = darray.from_zarr(zarray[-1])  # Convert zarr array to Dask array
#             max_val = darray.compute(dask_array.max())[0]
#             del dask_array
#             if 1 < max_val <= 255: #Image in 8bit col
#                 int_scale = 255
#             elif 255 < max_val <= 4095: # Image is 12bit colour, not 16! -> Checking actual values since Bits entry in XML lies and says 12bits for the Luca 8bit image
#                 int_scale = 4095
#             elif 4095 < max_val <= 65535:
#                 int_scale = 65535
#             else:
#                 raise NotImplementedError

#             md = full_res_tags
#             md["path"] = img
#             md["int_scale"] = int_scale

#             # Adding Image to viewer
#             viewer.add_image(
#                 zarray, name=img.stem, 
#                 scale=res_scale, 
#                 metadata=full_res_tags, contrast_limits=[0, int_scale])

#             empty_flag = False
    
#     for img in if_imgs:
#         if img.is_file():

#             # Loading Image data
#             image = tifffile.imread(img, aszarr=True)
#             image = zarr.open(image, "r") 
#             if isinstance(image, zarr.hierarchy.Group):
#                 zarray = [array for _, array in image.arrays()]
#             else:
#                 zarray = [image]
            
#             print(len(zarray), zarray[0], zarray[0].shape)

#             # Loading Image metadata
#             res_scale = (1,1)
#             with tifffile.TiffFile(img) as src:
#                 full_res_tags = {
#                     tag.name: tag.value for tag in src.series[0].pages[0].tags.values() 
#                     if tag.name not in [
#                         "StripOffsets", "StripByteCounts", "TileOffsets", 
#                         "TileByteCounts"] 
#                     and not isinstance(tag.value, numpy.ndarray)
#                 }
#                 full_res_tags["ImagePath"] = img
#                 try:
#                     if str(full_res_tags["ResolutionUnit"]) == "RESUNIT.CENTIMETER":
#                         xres = full_res_tags["XResolution"]
#                         yres = full_res_tags["YResolution"]
#                         x_scale = xres[1] / xres[0]
#                         y_scale = yres[1] / yres[0]
#                         scale = (x_scale, y_scale)
#                     else:
#                         raise NotImplementedError("Scaling supports only images in centimeters")
#                 except Exception as e:
#                     warning_noMD = warnings.warn(f"Could not detect resolution metadata for image \n {img.stem}. \n Exception: {e}")
#                     WarningNotification(warning_noMD)

#                 new_format = False
#                 xml = ElementTree.fromstring(src.series[0].pages[0].tags["ImageDescription"].value)
#                 if xml.find(".//LibraryAsJSON") is not None:
#                     import json
#                     dicti = json.loads(xml.find(".//LibraryAsJSON").text)
#                     if "spectra" in dicti.keys():
#                         new_format = True
#                         fluor_to_marker = {item["fluor"]: item["marker"] for item in dicti["spectra"] if "fluor" in item and "marker" in item}

#                 colmap_channels = {}
#                 for page in src.series[0].pages:
#                     xml = ElementTree.fromstring(page.tags["ImageDescription"].value)
#                     # tree = ElementTree.ElementTree(xml)
#                     # filename = f"page_{str(page)}_xml.xml"
#                     # tree.write(filename, encoding='utf-8', xml_declaration=True)
#                     if new_format == True:
#                         colmap_channels[
#                             xml.find(".//Responsivity/Band/Name").text
#                             ] = tuple(float(x) for x in xml.find(".//Color").text.split(","))
#                     else:
#                         colmap_channels[
#                             xml.find(".//Responsivity/Filter/Name").text
#                             ] = tuple(float(x) for x in xml.find(".//Color").text.split(","))

#                 colmap_channels = {key: tuple(
#                         v/255 if max(colmap_channels[key]) > 1 else v for v in val
#                     ) for key, val in colmap_channels.items()} 

#             dask_array = darray.from_zarr(zarray[-1])  # Convert zarr array to Dask array
#             max_val = darray.compute(dask_array.max())[0]
#             del dask_array
#             if 1 < max_val <= 255: #Image in 8bit col
#                 int_scale = 255
#             elif 255 < max_val <= 4095: # Image is 12bit colour, not 16! -> Checking actual values since Bits entry in XML lies and says 12bits for the Luca 8bit image
#                 int_scale = 4095
#             elif 4095 < max_val <= 65535:
#                 int_scale = 65535
#             else:
#                 raise NotImplementedError

#             if not load_mem:
#                 zarray = [darray.from_zarr(array) for array in zarray]

#             for index, (target, col) in enumerate(colmap_channels.items()):
#                 md = full_res_tags
#                 md["dye"] = target
#                 layer = md["dye"]
#                 md["path"] = img
#                 md["int_scale"] = int_scale
#                 if new_format == True:
#                     md["biomarker"] = fluor_to_marker[target]
#                     layer = md["biomarker"]

#                 cmap = Colormap(
#                     colors=numpy.array([(0, 0, 0, 1), col + (1,)]),
#                     name=target)

#                 channel_zarray = [array[index, :, :] for array in zarray]

#                 viewer.add_image(
#                     channel_zarray, name=f"{layer}_{img.stem}", 
#                     scale=scale, colormap=cmap, blending="additive", 
#                     metadata=md, contrast_limits=[0, int_scale])

#             empty_flag = False

#     if empty_flag == True: # Should the selection be empty it will return a warning on the GUI
#         warning_empty = warnings.warn("No image(s) selected for loading.")
#         WarningNotification(warning_empty)