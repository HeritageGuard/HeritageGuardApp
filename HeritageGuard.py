import os
import multiprocessing
from functools import partial
from tkinter import Tk

from UI.Views.DEMCompare import DEMCompare
from UI.Views.Panoramas import Panoramas
from constants import FRAME_TYPES
from Database.Database import Database
from Database.Datasets import Datasets
from UI.Button import UIButton
from UI.Container import Container
from UI.Image import UIImage
from UI.Views.Compare import Compare
from UI.Views.Dataset import Dataset
from UI.Views.Detection360 import Detection360

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


class HeritageGuard(object):
    def __init__(self, parent):
        """Constructor"""
        self.root = parent

        buttons_container = Container(
            root, pack_options={"side": "top", "fill": "x"})
        self.dataset_container = Container(
            root, pack_options={"fill": "both", "side": "left", "expand": True}
        )
        self.detection_360_container = Container(
            root, pack_options={"fill": "both", "side": "left", "expand": 1}
        )

        self.compare_container = Container(
            root, pack_options={"fill": "both", "side": "left", "expand": 1}
        )
        self.panoramas_container = Container(
            root, pack_options={"fill": "both", "side": "left", "expand": 1}
        )
        self.dem_compare_container = Container(
            root, pack_options={"fill": "both", "side": "left", "expand": 1}
        )

        self.containers = [
            self.dataset_container,
            self.detection_360_container,
            self.compare_container,
            self.panoramas_container,
            self.dem_compare_container
        ]

        button_options = {"padx": 5, "side": "left"}

        self.database = Database()
        datasets = Datasets(self.database.Session)

        all_datasets = datasets.all()

        UIImage(buttons_container.el, "./Assets/logo.jpg", 100, 100).show(
            {"padx": (0, 40), "side": "left"}
        )

        UIButton(
            buttons_container.el,
            "Datasets",
            partial(self.open_frame, FRAME_TYPES.DATASET)).show(button_options)

        UIButton(
            buttons_container.el,
            "Panoramas",
            partial(self.open_frame, FRAME_TYPES.PANORAMAS)).show(button_options)

        if len(all_datasets) > 0:
            UIButton(
                buttons_container.el,
                "Orto Photo",
                partial(self.open_frame, FRAME_TYPES.DETECT_360)).show(button_options)

            UIButton(
                buttons_container.el,
                "Compare",
                partial(self.open_frame, FRAME_TYPES.COMPARE)).show(button_options)

            UIButton(
                buttons_container.el,
                "DEM Compare",
                partial(self.open_frame, FRAME_TYPES.DEM_COMPARE)).show(button_options)

        UIButton(buttons_container.el, "Quit", root.destroy).show(
            {"side": "right", "padx": (0, 40)}
        )

        buttons_container.show()

        self.create_frames()
        self.open_frame(FRAME_TYPES.DATASET)

    def create_frames(self):
        dataset_view = Dataset(
            self.root, self.dataset_container.el, self.database.Session
        )
        detection_view = Detection360(
            self.root, self.detection_360_container.el, self.database.Session
        )
        compare_view = Compare(
            self.root, self.compare_container.el, self.database.Session
        )

        Panoramas(
            self.root, self.panoramas_container.el, self.database.Session
        )

        DEMCompare(self.root, self.dem_compare_container.el, self.database.Session)

        def open_dataset(name):
            detection_view.select_dataset(name)
            self.open_frame(FRAME_TYPES.DETECT_360)

        def open_element(dataset_id, element_id):
            detection_view.show_element(dataset_id, element_id)
            self.open_frame(FRAME_TYPES.DETECT_360)

        dataset_view.on("select", open_dataset)
        compare_view.on("select_element", open_element)

    def open_frame(self, frame_type):
        for container in self.containers:
            container.hide()
        self.containers[frame_type.value].show()


# Driver code
if __name__ == "__main__":
    multiprocessing.freeze_support()
    # create a GUI window
    root = Tk()

    # set the background colour of GUI window

    root.configure(background="#000")
    root.tk_setPalette(background="#000", foreground="#c4c4c4")

    # set the title of GUI window
    root.title("Heritage Guard Desktop App")

    # set the configuration of GUI window
    root.geometry("1000x800")

    app = HeritageGuard(root)

    # start the GUI
    root.mainloop()
