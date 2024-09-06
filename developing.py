from napari import Viewer, run
from napari.settings import get_settings

settings = get_settings()
settings.experimental.async_ = True
settings.experimental.autoswap_buffers = True

viewer = Viewer()
viewer.scale_bar.visible = False
viewer.scale_bar.colored = True
viewer.scale_bar.unit = "cm"

dock_widget, plugin_widget = viewer.window.add_plugin_dock_widget(
    "popidd-reader", "Image Loader",
    tabify=False
)

run()