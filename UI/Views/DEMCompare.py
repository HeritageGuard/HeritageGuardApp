import os
import subprocess
from multiprocessing import Pool
from pathlib import Path
from tkinter.filedialog import askopenfile
import shapefile

from Backend.DirectoryHelper import DirectoryHelper
from Backend.ExecutableProvider import ExecutableProvider
from UI.Button import UIButton
from UI.Container import Container
from UI.OptionMenu import DictVar, OptionMenu
from UI.ProgressBar import ProgressBar
from UI.ScrollableImage import ScrollableImage
from UI.Text import Text
from UI.TextButton import TextButton
from UI.Views.View import View


class DEMCompare(View):
    def __init__(self, root, container, session):
        super(DEMCompare, self).__init__(root, container, session)

        self.inputs_container = Container(
            self.container, pack_options={
                "side": "top", "anchor": "n", "pady": 10}
        )

        all_datasets = self.database.datasets.all()
        menu_options = dict([[d.id, d.title] for d in all_datasets])

        self.first_dataset = DictVar(int_string_dict=menu_options)
        self.second_dataset = DictVar(int_string_dict=menu_options)

        self.dataset_a = None
        self.dataset_b = None

        if len(all_datasets) > 0:
            self.first_dataset.set(all_datasets[0].id)
        if len(all_datasets) > 1:
            self.second_dataset.set(all_datasets[1].id)

        Text(self.inputs_container.el, "Select first dataset:").show(
            {"side": "left", "anchor": "n"})

        self.first_dataset_input = OptionMenu(
            self.inputs_container.el, self.first_dataset, menu_options
        )
        self.first_dataset_input.pack({"side": "left", "anchor": "n", "padx": 10})

        Text(self.inputs_container.el, "Select second dataset:").show(
            {"side": "left", "anchor": "n"})
        self.second_dataset_input = OptionMenu(
            self.inputs_container.el, self.second_dataset, menu_options
        )
        self.second_dataset_input.pack({"side": "left", "anchor": "n", "padx": 10})

        UIButton(self.inputs_container.el, "Compare",
                 self.compare).show({"side": "left", "anchor": "n", "padx": 5})

        self.dataset_a_button = UIButton(self.inputs_container.el, "Image A", self.show_image_a)

        self.dataset_b_button = UIButton(self.inputs_container.el, "Image B", self.show_image_b)

        self.save_button = UIButton(self.inputs_container.el, "Save", self.save_canvas)

        self.scrollable_image = None
        self.showing_image_a = True

        self.inputs_container.show()

    def compare(self):
        progress_bar = ProgressBar(self.container, self.root, pack_options={"expand": 1, "fill": "x"})
        progress_bar.show()
        progress_bar.set_value(0, 'Loading data')
        self.dataset_a = self.database.datasets.get_by_id(self.first_dataset.get_int())
        self.dataset_b = self.database.datasets.get_by_id(self.second_dataset.get_int())

        if self.scrollable_image is not None:
            self.scrollable_image.hide()
        else:
            self.scrollable_image = ScrollableImage(self.container, image_a_path=self.dataset_a.orto_photo_path, image_b_path=self.dataset_b.orto_photo_path, root=self.root)

        qgis_exec = ExecutableProvider.qgis()
        temp_path = DirectoryHelper.ensure_exists("temp")
        temp_file = temp_path + '/Final.shp'
        model_path = os.path.abspath('Models/model.model3')
        dem_a_path = self.dataset_a.height_map_path
        dem_b_path = self.dataset_b.height_map_path
        if os.name == 'nt':
            temp_file = temp_file.replace('\\', '/')
            model_path = model_path.replace('\\', '/')

        command = r'{} run {} --verbose -- native:smoothgeometry_1:OUTPUT="{}" dema="{}" demb="{}"'.format(qgis_exec, model_path, temp_file, dem_a_path, dem_b_path)

        if os.name == 'nt':
            command = r'"{}" run {} --verbose -- native:smoothgeometry_1:OUTPUT="{}" dema="{}" demb="{}"'.format(qgis_exec, model_path, temp_file, dem_a_path, dem_b_path)

        progress_bar.set_value(40, 'Analyzing height maps')
        # subprocess.run(command)
        process = subprocess.Popen(args=command, stdout=subprocess.PIPE, shell=True)
        # stdout, stderr = process.communicate()
        progress_bar.set_value(80, 'Generating report')
        shapes = shapefile.Reader(temp_file)

        progress_bar.set_value(90, 'Generating report')
        self.scrollable_image.add_polygons(shapes.shapes(), self.dataset_a.orto_photo_path)
        progress_bar.set_value(100, 'Done!')
        progress_bar.destroy()

        self.dataset_a_button.show({"side": "left", "anchor": "n", "padx": 5})
        self.dataset_b_button.show({"side": "left", "anchor": "n", "padx": 5})
        self.save_button.show({"side": "left", "anchor": "n", "padx": 5})
        self.scrollable_image.show()

    def show_image_a(self):
        self.showing_image_a = True
        self.scrollable_image.show_image(True)

    def show_image_b(self):
        self.showing_image_a = False
        self.scrollable_image.show_image(False)

    def save_canvas(self):
        self.scrollable_image.save(self.showing_image_a)