"""
This module contains four napari widgets declared in
different ways:

- a pure Python function flagged with `autogenerate: true`
    in the plugin manifest. Type annotations are used by
    magicgui to generate widgets for each parameter. Best
    suited for simple processing tasks - usually taking
    in and/or returning a layer.
- a `magic_factory` decorated function. The `magic_factory`
    decorator allows us to customize aspects of the resulting
    GUI, including the widgets associated with each parameter.
    Best used when you have a very simple processing task,
    but want some control over the autogenerated widgets. If you
    find yourself needing to define lots of nested functions to achieve
    your functionality, maybe look at the `Container` widget!
- a `magicgui.widgets.Container` subclass. This provides lots
    of flexibility and customization options while still supporting
    `magicgui` widgets and convenience methods for creating widgets
    from type annotations. If you want to customize your widgets and
    connect callbacks, this is the best widget option for you.
- a `QWidget` subclass. This provides maximal flexibility but requires
    full specification of widget layouts, callbacks, events, etc.

References:
- Widget specification: https://napari.org/stable/plugins/guides.html?#widgets
- magicgui docs: https://pyapp-kit.github.io/magicgui/

Replace code below according to your needs.
"""
from typing import TYPE_CHECKING

import warnings
from napari.utils.notifications import WarningNotification

from pathlib import Path
from magicgui import magic_factory
import napari.layers

import numpy

from ._image import load_img
from ._anno import load_geojson

if TYPE_CHECKING:
    import napari


def image_reader(
    viewer: "napari.Viewer",
    bf_imgs = Path(""),
    if_imgs = Path(""),
    load_mem = bool
):
    empty_flag = True
    for img in bf_imgs:
        if img.is_file():
            img_layer_data = load_img(img, modality="BF", load_mem=load_mem)
            for i in img_layer_data: #unpacking list of tuples even if BF images should only have 1 layer per image
                viewer.add_layer(napari.layers.Layer.create(*i)) #unpack tuple as func uses positional args
                # viewer._add_layer_from_data(*i) #use this one if channel_axis present
            empty_flag = False
    for img in if_imgs:
        if img.is_file():
            img_layer_data = load_img(img, modality="IF", load_mem=load_mem)
            for i in img_layer_data:
                viewer.add_layer(napari.layers.Layer.create(*i))
            empty_flag = False
    if empty_flag is True: # Should the selection be empty it will return a warning on the GUI
        warning_empty = warnings.warn("No image(s) selected for loading.")
        WarningNotification(warning_empty)

#Test magic factory usage directly (not as decorator)
wLoadImage = magic_factory(function=image_reader,
        bf_imgs = {
            "label":"Brightfield image(s)", 
            "widget_type":"FileEdit", "mode":"rm",
            "filter":"*.tiff;*.tif;*.svs;*.ndpi"
            },  
        if_imgs = {
            "label":"Fluorescence image(s)", 
            "widget_type":"FileEdit", "mode":"rm",
            "filter":"*.tiff;*.tif;*qptiff"
            },
        load_mem = {
            "widget_type": "CheckBox", "value": False, 
            "text": "Load full image(s) into memory"
            },
        call_button = "Load image(s)")


def anno_reader(
        viewer: "napari.Viewer",
        image: "napari.layers.Image",
        anno_paths = Path(""),
):
    for anno in anno_paths:
        shape_layer_data = load_geojson(anno)
        for i in shape_layer_data:
            i[1]["scale"] = image.scale*numpy.array([-1,1])
            viewer.add_layer(napari.layers.Layer.create(*i))
wLoadAnno = magic_factory(function=anno_reader,
        image = {"label":"Image layer"},
        anno_paths = {
            "label":"Annotation GEOJSON",
            "widget_type": "FileEdit", "mode": "rm", 
            "filter":"*.geojson"
            },
        call_button="Load Annotation"
        )


# from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget
# from magicgui.widgets import CheckBox, Container, create_widget
# from skimage.util import img_as_float

    # # Uses the `autogenerate: true` flag in the plugin manifest
    # # to indicate it should be wrapped as a magicgui to autogenerate
    # # a widget.
    # def threshold_autogenerate_widget(
    #     img: "napari.types.ImageData",
    #     threshold: "float",
    # ) -> "napari.types.LabelsData":
    #     return img_as_float(img) > threshold


    # # the magic_factory decorator lets us customize aspects of our widget
    # # we specify a widget type for the threshold parameter
    # # and use auto_call=True so the function is called whenever
    # # the value of a parameter changes
    # @magic_factory(
    #     threshold={"widget_type": "FloatSlider", "max": 1}, auto_call=True
    # )
    # def threshold_magic_widget(
    #     img_layer: "napari.layers.Image", threshold: "float"
    # ) -> "napari.types.LabelsData":
    #     return img_as_float(img_layer.data) > threshold

    # # if we want even more control over our widget, we can use
    # # magicgui `Container`
    # class ImageThreshold(Container):
    #     def __init__(self, viewer: "napari.viewer.Viewer"):
    #         super().__init__()
    #         self._viewer = viewer
    #         # use create_widget to generate widgets from type annotations
    #         self._image_layer_combo = create_widget(
    #             label="Image", annotation="napari.layers.Image"
    #         )
    #         self._threshold_slider = create_widget(
    #             label="Threshold", annotation=float, widget_type="FloatSlider"
    #         )
    #         self._threshold_slider.min = 0
    #         self._threshold_slider.max = 1
    #         # use magicgui widgets directly
    #         self._invert_checkbox = CheckBox(text="Keep pixels below threshold")

    #         # connect your own callbacks
    #         self._threshold_slider.changed.connect(self._threshold_im)
    #         self._invert_checkbox.changed.connect(self._threshold_im)

    #         # append into/extend the container with your widgets
    #         self.extend(
    #             [
    #                 self._image_layer_combo,
    #                 self._threshold_slider,
    #                 self._invert_checkbox,
    #             ]
    #         )

    #     def _threshold_im(self):
    #         image_layer = self._image_layer_combo.value
    #         if image_layer is None:
    #             return

    #         image = img_as_float(image_layer.data)
    #         name = image_layer.name + "_thresholded"
    #         threshold = self._threshold_slider.value
    #         if self._invert_checkbox.value:
    #             thresholded = image < threshold
    #         else:
    #             thresholded = image > threshold
    #         if name in self._viewer.layers:
    #             self._viewer.layers[name].data = thresholded
    #         else:
    #             self._viewer.add_labels(thresholded, name=name)


    # class ExampleQWidget(QWidget):
    #     # your QWidget.__init__ can optionally request the napari viewer instance
    #     # use a type annotation of 'napari.viewer.Viewer' for any parameter
    #     def __init__(self, viewer: "napari.viewer.Viewer"):
    #         super().__init__()
    #         self.viewer = viewer

    #         btn = QPushButton("Click me!")
    #         btn.clicked.connect(self._on_click)

    #         self.setLayout(QHBoxLayout())
    #         self.layout().addWidget(btn)

    #     def _on_click(self):
    #         print("napari has", len(self.viewer.layers), "layers")

