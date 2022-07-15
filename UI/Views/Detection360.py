import gc
import importlib
from copy import copy
from functools import partial
from pathlib import Path
from tkinter.filedialog import askopenfile

import os
import geopandas as gpd
import numpy as np
from geojson import Point

from Backend.DirectoryHelper import DirectoryHelper
from Backend.Helpers import area_from_bbox
from Backend.PointCloudTools import PointCloudTools
from Backend.Transformer import Transformer
from UI.AdvancedImage import AdvancedImage
from UI.Button import UIButton
from UI.Container import Container
from UI.OptionMenu import DictVar, OptionMenu
from UI.PointCloudViewer import PointCloudViewer
from UI.ProgressBar import ProgressBar
from UI.Table import Header, Table
from UI.Text import Text
from UI.TextButton import TextButton
from UI.Views.View import View


class Detection360(View):
    def __init__(self, root, container, session):
        super(Detection360, self).__init__(root, container, session)
        Text(self.container, "Orto photo").show(
            {"fill": "both", "side": "top"})

        self.active_image = None
        self.active_element = None
        self.Neighbours = None

        # Create inputs
        self.inputs_container = Container(
            self.container, pack_options={
                "side": "top", "anchor": "n", "pady": 10}
        )

        self.file = TextButton(
            self.inputs_container.el,
            "Select orto photo (.jpg or .png)",
            partial(
                self.open_file,
                0,
                [
                    ("Image File", "*.jpg"),
                    ("Image File", "*.JPG"),
                    ("Image File", "*.png"),
                    ("Image File", "*.PNG"),
                ],
            ),
        )

        self.file_tif = TextButton(
            self.inputs_container.el,
            "Select height map (.tif)",
            partial(
                self.open_file, 1, [("Image File", "*.tif"),
                                    ("Image File", "*.TIF")]
            ),
        )

        self.file_ept = TextButton(
            self.inputs_container.el,
            "Select point cloud (.json)",
            partial(
                self.open_file, 2, [("Image File", "*.json"),
                                    ("Image File", "*.JSON")]
            ),
        )

        self.file_kvr = TextButton(
            self.inputs_container.el,
            "Select data gis layer (.shp)",
            partial(
                self.open_file, 3, [("Shape File", "*.shp"),
                                    ("Shape File", "*.SHP")]
            ),
        )

        self.file_inputs = [self.file, self.file_tif, self.file_ept, self.file_kvr]

        for file_input in self.file_inputs:
            file_input.show()

        UIButton(self.inputs_container.el, "Process",
                 self.process).show({"pady": 5})
        # UIButton(self.container, 'Process point clouds', self.process_point_clouds).show({'pady': 5})

        self.selected_value = None
        self.dataset_input = None
        data_headers = Header.headers_from_list(
            [
                {"title": "Id", "method": self.show_image, "width": 50},
                {"title": "File id", "method": self.show_image, "width": 50},
                {"title": "ElementType", "method": self.show_image, "width": 200},
                "Lat",
                "Lon",
                "Height",
                "Score",
                "Area",
                "Address"
            ]
        )

        self.data_table = Table(self.container, data_headers, delete_method=self.delete_element)
        for type in ["Stoglangiai", "Turiniai stoglangiai", "Kaminai"]:
            self.data_table.add_menu_action("Set type to " + type, partial(self.set_element_type, type))

        self.info = Table(
            self.container,
            Header.headers_from_list(
                [{"title": "Key", "width": 180}, "value"]),
            show_row_index=False,
            show_scrollbars=False,
        )

        self.point_cloud_viewer = PointCloudViewer(
            self.container, self.database)

    def show_inputs_or_load(self, *args):
        if self.database.elements.any_by_dataset_id(
                self.selected_value.get_int()):
            self.load_as_table()
            self.inputs_container.hide()
        else:
            self.data_table.hide()
            self.point_cloud_viewer.hide()
            self.info.hide()
            if self.active_image is not None:
                self.active_image.hide()
            self.inputs_container.show()

    def select_dataset(self, id):
        all_datasets = self.database.datasets.all()
        menu_options = dict([[d.id, d.title] for d in all_datasets])

        self.selected_value = DictVar(int_string_dict=menu_options)
        self.selected_value.trace("w", self.show_inputs_or_load)
        if len(all_datasets) > 0:
            self.selected_value.set(all_datasets[0].id)

        if self.dataset_input:
            self.dataset_input.destroy()
            self.dataset_input = None

        self.dataset_input = OptionMenu(
            self.container, self.selected_value, menu_options
        )
        self.dataset_input.pack({"pady": 10})
        self.selected_value.set(id)
        self.show_inputs_or_load()

    def clear(self):
        # clear the content of text entry box
        # self.dataset_input.clear()
        self.file.clear()

    # Function to take data from GUI
    # window and write to database
    def process(self):
        OrtoPhotoModule = importlib.import_module("Backend.OrtoPhoto")
        AIModule = importlib.import_module("Backend.AI")
        OrtoImage = OrtoPhotoModule.OrtoImage
        PredictOrto = AIModule.PredictOrto
        DEMImage = OrtoPhotoModule.DEMImage

        progress_bar = ProgressBar(
            self.container, self.root, pack_options={"expand": 1, "fill": "x"}
        )
        progress_bar.show()

        dataset_id = self.selected_value.get_int()

        if dataset_id is None:
            return False

        class_names = [
            "BG",
            "objects",
            "Stoglangiai",
            "Turiniai stoglangiai",
            "Kaminai",
            "classifications",
        ]
        orto_image_path = self.file.get_hidden()
        orto_image = OrtoImage(orto_image_path)

        dem_image_path = self.file_tif.get_hidden()
        dem = DEMImage(dem_image_path)
        ept_file_name = self.file_ept.get_hidden()

        gis_data = gpd.read_file(self.file_kvr.get_hidden(), crs={'init': 'epsg:3346'})
        predict_orto = PredictOrto()
        image_size = 800
        predict_orto.initRCNN()

        dataset = self.database.datasets.get_by_id(dataset_id)
        setattr(dataset, 'orto_photo_path', orto_image_path)
        setattr(dataset, 'height_map_path', dem_image_path)
        setattr(dataset, 'point_cloud_path', ept_file_name)

        all_windows = int((orto_image.width / image_size) * (orto_image.height / image_size))
        i = 0

        for col_index, col in orto_image.cut_up_2(image_size, 100):
            for row_index, window in enumerate(col):
                self.process_image(orto_image, window, col_index, row_index, progress_bar, i, all_windows, predict_orto,
                                   dataset_id, dem, class_names, ept_file_name, gis_data)
                i = i + 1

        progress_bar.destroy()
        self.load_as_table()

    def process_image(self, orto_image, window, col_index, row_index, progress_bar, i, all_windows, predict_orto,
                      dataset_id, dem, class_names, ept_file_name, gis_data):
        self.root.update_idletasks()
        progress_bar.set_value(int((i / all_windows) * 100), 'Processing frame {}/{}'.format(i, all_windows))

        img = np.moveaxis(
            np.asarray(orto_image.raster.read(window=window)), 0, 2
        )

        results = predict_orto.detect_instances_single(img)

        if len(results[0]["rois"]) > 0:
            file_id = self.database.files.add(
                {
                    "filename": "orto_" + str(col_index) + "_" + str(row_index),
                    "meta": "",
                    "dataset_id": dataset_id,
                    "content": img.tobytes(),
                    "width": img.shape[0],
                    "height": img.shape[1],
                }
            )
            self.process_results(results[0], orto_image, window, dem, file_id, dataset_id, class_names, ept_file_name,
                                 gis_data)
        else:
            del img
        del results
        gc.collect()

    def process_results(self, result, orto_image, window, dem, file_id, dataset_id, class_names, ept_file_name,
                        gis_data):
        for index, bbox in enumerate(result["rois"]):
            class_id = result["class_ids"][index]
            score = result["scores"][index]

            (x, y) = self._get_box_center(bbox)
            (lat, lon) = orto_image.xy_window(x, y, window)
            height = dem.get_elevation(lat, lon)
            gis_data_result = self.get_gis_data(lat, lon, gis_data)
            address = ''
            status = ''
            name = ''
            code = None
            if len(gis_data_result) > 0:
                name = gis_data_result.Name[0]
                status = gis_data_result.Status[0]
                code = int(gis_data_result.Code[0])

            data = {
                "file_id": file_id,
                "dataset_id": dataset_id,
                "element_type": class_names[class_id],
                "score": score,
                "height": height,
                "lat": lat,
                "lon": lon,
                "bbox": bbox,
                "address": address,
                "status": status,
                "name": name,
                "code": code
            }
            element_id = self.database.elements.add(data)
            DirectoryHelper.ensure_exists('./data/' + str(dataset_id))
            output_file_name = os.path.abspath('./data/' + str(dataset_id) + '/' + str(element_id) + '.las')
            if os.name == 'nt':
                output_file_name = output_file_name.replace('\\', '/')
            point_cloud_saved = self.prepare_point_cloud(lat, lon, height, ept_file_name, output_file_name, area_from_bbox(bbox))

            if not point_cloud_saved:
                self.database.elements.delete(element_id)

        del result

    def prepare_point_cloud(self, lat, lon, height, file_name, output_file_name,  area):
        radius = 5
        distance = area / 5000
        if distance < 2:
            distance = 2
        if distance > 5:
            distance = 5

        return PointCloudTools.crop_to_file(file_name, output_file_name, lat, lon, height, distance)

    def load_as_table(self):
        if self.Neighbours is None:
            self.Neighbours = importlib.import_module(
                "Backend.Neighbours").Neighbours
        neighbours = self.Neighbours()
        dataset_id = self.selected_value.get_int()

        all_elements = self.database.elements.get_by_dataset_id(dataset_id)
        # gis_address_data = gpd.read_file(os.path.abspath('./demo_data/gis-layers/KV_P.shp'),
        #                                  crs={'init': 'epsg:3346'})
        # for element in all_elements:
        #     data = self.get_gis_data(element.lat, element.lon, gis_address_data, fields=['Address'], area_field='Shape_Area')
        #     setattr(element, 'address', data.Address[0] or '')
        # self.database.commit()

        all_elements = neighbours.Process(
            all_elements, test_radius=4, deviation=0.5)
        all_elements.sort(key=lambda x: (x.correlation_id, x.area))

        self.data_table.show(
            {"side": "top", "expand": 1, "fill": "both", "padx": 30, "pady": 10}
        )

        data = [
            [
                element.id,
                element.file_id,
                element.element_type,
                element.lat,
                element.lon,
                element.height,
                element.score,
                element.area,
                element.address
            ]
            for element in all_elements
        ]
        self.data_table.add_data(data)

    def get_gis_data(self, lat, lon, data, fields=None, area_field="SHAPE_Area"):
        if fields is None:
            fields = ['Code', 'Name', 'Status']
        data_frame = copy(data)
        lat, lon = Transformer().transformer.transform(lat, lon)
        point = Point((lon, lat))
        point_data = gpd.GeoDataFrame(crs=3346, geometry=[point])
        point_geometry = point_data.iloc[0]['geometry']
        data_frame['distances'] = data_frame.distance(point_geometry)
        return data_frame.query('distances<=5').sort_values(by=area_field)[fields].to_records()

    def show_image(self, data=None):
        file_id = int(data[1])
        image = self.database.files.get_by_id(file_id)

        if self.active_image:
            self.active_image.clear()
            if self.active_image.id != file_id:
                self.active_image.replace_image(image)
                self.active_image.id = file_id
        else:
            self.active_image = AdvancedImage(
                self.container, id=file_id, image_data=image
            )
            self.active_image.show({"anchor": "s", "side": "left"})

        for element in self.database.elements.get_by_file_id(image.id):
            if element.id == int(data[0]):
                self.active_element = element
                self.show_info(element.__dict__)
            self.active_image.add_point(
                element.__dict__, self.select_element, current=False
            )

        self.active_image.add_point(
            self.active_element.__dict__, self.select_element, current=True
        )

    def set_element_type(self, type, id, _, row_index):
        element = self.database.elements.get_by_id(int(id))
        element.element_type = type
        self.database.commit()
        self.data_table.table.set_cell_data(row_index, 2, value=type, redraw=True)

    def show_image_related(self, data=None):
        related_ids = data[9].split(" ")
        if len(related_ids) > 0 and len(related_ids[0]) > 0:
            id_to_show = int(related_ids[0])
            if id_to_show:
                self.data_table.find_by_id(id_to_show)

    def open_file(self, index, file_types):
        opened_file = askopenfile(filetypes=file_types)
        if opened_file:
            filePath = opened_file.name
            self.file_inputs[index].set(Path(filePath).name)
            self.file_inputs[index].set_hidden(filePath)

    def select_element(self, info):
        self.show_info(info)
        self.data_table.find_by_id(info["id"])

    def delete_element(self, id):
        self.database.elements.delete(id)

    def show_element(self, dataset_id, element_id):
        self.select_dataset(dataset_id)
        self.data_table.find_by_id(element_id)

    def show_info(self, info):
        info_copy = dict(info)
        del info_copy["_sa_instance_state"]
        info_copy["area"] = area_from_bbox(info_copy["bbox"])
        self.info.add_data([[x[0], x[1]] for x in info_copy.items()])
        self.info.show({"anchor": "w", "side": "left", "padx": 10})
        self.point_cloud_viewer.show()
        self.point_cloud_viewer.open_point_cloud(info["id"])

    @staticmethod
    def _get_box_center(bbox):
        x = (bbox[2] - bbox[0]) / 2
        y = (bbox[3] - bbox[1]) / 2
        return bbox[0] + x, bbox[1] + y

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2, **kwarg):
        R = 6371.0088
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * \
            np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arctan2(a ** 0.5, (1 - a) ** 0.5)
        d = R * c
        return round(d * 1000, 4)
