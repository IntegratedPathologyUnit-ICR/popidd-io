from napari import Viewer, run

viewer = Viewer()

dock_widget, plugin_widget = viewer.window.add_plugin_dock_widget(
    "popidd-reader", "Image Loader",
    tabify=False
)

run()