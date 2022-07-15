import numpy as np

from Backend.DirectoryHelper import DirectoryHelper
from Backend.ExecutableProvider import ExecutableProvider
from Backend.Helpers import area_from_bbox
from Backend.Neighbours import Neighbours
from Backend.OrtoPhoto import OrtoImage
from Backend.PointCloudTools import PointCloudTools
from Backend.ReportBuilder import ReportBuilder
from UI.AdvancedImage import AdvancedImage
from UI.Button import UIButton
from UI.Container import Container
from UI.OptionMenu import DictVar, OptionMenu
from UI.PointCloudViewer import PointCloudViewer
from UI.ProgressBar import ProgressBar
from UI.Table import Header, Table
from UI.Text import Text
from UI.Views.View import View


class Compare(View):
    def __init__(self, root, container, session):
        super(Compare, self).__init__(root, container, session)

        self.inputs_container = Container(
            self.container, pack_options={
                "side": "top", "anchor": "n", "pady": 10}
        )

        all_datasets = self.database.datasets.all()
        menu_options = dict([[d.id, d.title] for d in all_datasets])

        self.first_dataset = DictVar(int_string_dict=menu_options)
        self.second_dataset = DictVar(int_string_dict=menu_options)

        if len(all_datasets) > 0:
            self.first_dataset.set(all_datasets[0].id)
        if len(all_datasets) > 1:
            self.second_dataset.set(all_datasets[1].id)

        Text(self.inputs_container.el, "Select first dataset:").show(
            {"side": "left", "anchor": "n"})

        self.first_dataset_input = OptionMenu(
            self.inputs_container.el, self.first_dataset, menu_options
        )
        self.first_dataset_input.pack({"side": "left", "anchor": "n", "padx": 100})

        Text(self.inputs_container.el, "Select second dataset:").show(
            {"side": "left", "anchor": "n"})
        self.second_dataset_input = OptionMenu(
            self.inputs_container.el, self.second_dataset, menu_options
        )
        self.second_dataset_input.pack({"side": "left", "anchor": "n", "padx": 10})

        UIButton(self.inputs_container.el, "Compare",
                 self.compare).show({"side": "left", "anchor": "n", "padx": 5})

        self.save_button = UIButton(self.inputs_container.el, "Save report",
                                    self.save_report)

        self.image_A = None
        self.image_B = None
        self.point_cloud_viewer = None
        self.orto_image_a = None
        self.orto_image_b = None
        self.point_cloud_a_file_path = None
        self.point_cloud_b_file_path = None

        data_headers = Header.headers_from_list(
            [
                {"title": "Id", "method": self.show_image, "width": 50},
                {"title": "File id", "method": self.show_image, "width": 50},
                {"title": "KVR Code", "width": 50},
                {"title": "ElementType", "method": self.show_image, "width": 200},                "Lat",
                "Lon",
                "Height",
                "Score",
                {"title": "Address", "width": 200},
                {"title": "Reason", "method": self.show_image, "width": 200},
                {"title": "E2 Id", "width": 50},
                {"title": "E2 FId", "width": 50},
                {"title": "Histograms", "width": 300},
                "Coefficient"
            ]
        )

        self.data_table = Table(self.container, data_headers)
        self.data_table.add_menu_action("Explore A", self.show_element_in_a)
        self.data_table.add_menu_action("Explore B", self.show_element_in_b)
        self.data_table.add_menu_action("Set both types to A", self.set_both_types_to_a)
        self.data_table.add_menu_action("Set both types to B", self.set_both_types_to_b)
        self.data_table.add_menu_action("Remove from report", self.remove_from_report)
        self.data_table.add_menu_action("[!!!] Delete in both datasets", self.delete_in_both_datasets)
        self.data_table.add_menu_action("[!!!] Delete in dataset A", self.delete_in_dataset_a)
        self.data_table.add_menu_action("[!!!] Delete in dataset B", self.delete_in_dataset_b)

        self.inputs_container.show()

    def compare(self):
        progress_bar = ProgressBar(self.container, self.root, pack_options={"expand": 1, "fill": "x"})
        progress_bar.show()
        progress_bar.set_value(0, 'Loading data')
        dataset_a = self.database.datasets.get_by_id(self.first_dataset.get_int())
        dataset_b = self.database.datasets.get_by_id(self.second_dataset.get_int())
        data_a = self.database.elements.get_by_dataset_id(dataset_a.id)
        data_b = self.database.elements.get_by_dataset_id(dataset_b.id)
        self.orto_image_a = OrtoImage(dataset_a.orto_photo_path)
        self.orto_image_b = OrtoImage(dataset_b.orto_photo_path)
        self.point_cloud_a_file_path = dataset_a.point_cloud_path
        self.point_cloud_b_file_path = dataset_b.point_cloud_path

        neighbours = Neighbours()

        progress_bar.set_value(20, 'Loading dataset A')
        data_a = neighbours.Process(data_a, test_radius=4, deviation=0.5)
        progress_bar.set_value(40, 'Loading dataset B')
        data_b = neighbours.Process(data_b, test_radius=4, deviation=0.5)

        progress_bar.set_value(50, 'Processing datasets')
        elements_not_in_A, elements_not_in_B, differing_items, other_elements = neighbours.Compare(data_a, data_b)

        table_data_a = [
            [
                '-',
                '-',
                element.code or '-',
                element.element_type,
                element.lat,
                element.lon,
                element.height,
                element.score,
                element.address,
                'Appeared in ' + self.second_dataset.get(),
                element.id,
                element.file_id,
                '',
                0
            ]
            for element in elements_not_in_A
        ]

        for index, element in enumerate(elements_not_in_A):
            progress_bar.set_value(60, 'Calculating histograms {}/{}'.format(index, len(elements_not_in_A)))
            coefficient, histograms = PointCloudTools.compare_point_clouds(element, element, dataset_a, dataset_b)
            table_data_a[index][-1] = coefficient
            table_data_a[index][-2] = histograms

        table_data_b = [
            [
                element.id,
                element.file_id,
                element.code or '-',
                element.element_type,
                element.lat,
                element.lon,
                element.height,
                element.score,
                element.address,
                'Disappeared in ' + self.second_dataset.get(),
                '-',
                '-',
                '',
                0
            ]
            for element in elements_not_in_B
        ]

        for index, element in enumerate(elements_not_in_B):
            progress_bar.set_value(70, 'Calculating histograms {}/{}'.format(index, len(elements_not_in_B)))
            coefficient, histograms = PointCloudTools.compare_point_clouds(element, element, dataset_a, dataset_b)
            table_data_b[index][-1] = coefficient
            table_data_b[index][-2] = histograms

        diff = np.array([
            [
                element[0].id,
                element[0].file_id,
                element[0].code or '-',
                element[0].element_type,
                element[0].lat,
                element[0].lon,
                element[0].height,
                element[0].score,
                element[0].address,
                'Elements differ ' + element[1].element_type,
                element[1].id,
                element[1].file_id,
                '',
                0
            ]
            for element in differing_items
        ])

        for index, element in enumerate(differing_items):
            progress_bar.set_value(80, 'Calculating histograms {}/{}'.format(index, len(differing_items)))
            coefficient, histograms = PointCloudTools.compare_point_clouds(element[0], element[1], dataset_a, dataset_b)
            diff[index][-1] = coefficient
            diff[index][-2] = histograms

        changed_elements = np.array([
            [
                element[0].id,
                element[0].file_id,
                element[0].code or '-',
                element[0].element_type,
                element[0].lat,
                element[0].lon,
                element[0].height,
                element[0].score,
                element[0].address,
                'Element changed',
                element[1].id,
                element[1].file_id,
                '',
                0
            ]
            for element in other_elements
        ])

        for index, element in enumerate(other_elements):
            progress_bar.set_value(90, 'Calculating histograms {}/{}'.format(index, len(other_elements)))
            coefficient, histograms = PointCloudTools.compare_point_clouds(element[0], element[1], dataset_a, dataset_b)
            changed_elements[index][-1] = coefficient
            changed_elements[index][-2] = histograms
        progress_bar.set_value(95, 'Preparing report')
        all_elements = np.concatenate((table_data_a, table_data_b, changed_elements)).tolist()
        all_elements = [x for x in all_elements
                        if not x[-2].endswith("100.0]") and not x[-2].endswith("nan]") and 15 > float(x[-1]) > -1000]
        all_elements = np.concatenate((all_elements, diff)).tolist() if len(all_elements) > 0 else diff
        progress_bar.set_value(100, 'Done')
        progress_bar.destroy()
        self.data_table.show(
            {"side": "top", "expand": 1, "fill": "both", "padx": 30, "pady": 10}
        )
        self.data_table.add_data(all_elements)
        self.save_button.show({"side": "left", "anchor": "n", "padx": 5})
        if self.point_cloud_viewer is None:
            self.point_cloud_viewer = PointCloudViewer(
                self.container, self.database)

    def show_element_in_a(self, id, *args):
        self.emit('select_element', int(self.first_dataset.get_int()), int(id))

    def show_element_in_b(self, _, row_data, *args):
        self.emit('select_element', int(self.second_dataset.get_int()), int(row_data[10]))

    def set_both_types_to_a(self, id, row_data, row_index):
        element_a = self.database.elements.get_by_id(int(id))
        element_b = self.database.elements.get_by_id(int(row_data[10]))
        element_b.element_type = element_a.element_type
        self.database.commit()
        self.data_table.table.delete_row(row_index, deselect_all=True)

    def set_both_types_to_b(self, id, row_data, row_index):
        element_a = self.database.elements.get_by_id(int(id))
        element_b = self.database.elements.get_by_id(int(row_data[10]))
        element_a.element_type = element_b.element_type
        self.database.commit()
        self.data_table.table.delete_row(row_index, deselect_all=True)

    def delete_in_both_datasets(self, id, row_data, row_index):
        self.database.elements.delete(int(id))
        self.database.elements.delete(int(row_data[10]))
        self.data_table.table.delete_row(row_index, deselect_all=True)

    def delete_in_dataset_a(self, id, _, row_index):
        self.database.elements.delete(int(id))
        self.data_table.table.delete_row(row_index, deselect_all=True)

    def delete_in_dataset_b(self, _, row_data, row_index):
        self.database.elements.delete(int(row_data[10]))
        self.data_table.table.delete_row(row_index, deselect_all=True)

    def remove_from_report(self, _, __, row_index):
        self.data_table.table.delete_row(row_index, deselect_all=True)

    def save_report(self):
        dataset_a = self.database.datasets.get_by_id(self.first_dataset.get_int())
        dataset_b = self.database.datasets.get_by_id(self.second_dataset.get_int())
        ReportBuilder.build(self.data_table.table.get_sheet_data(), dataset_a, dataset_b)

    def show_image(self, data):
        if data[0] != '-' and data[10] != '-':
            element = self.database.elements.get_by_id(int(data[0]))
            image = self.database.files.get_by_id(element.file_id)
            self.show_image_internal(element, image)

            second_element = self.database.elements.get_by_id(int(data[10]))
            second_image = self.database.files.get_by_id(second_element.file_id)
            self.show_image_internal(second_element, second_image, 'image_B')
            self.point_cloud_viewer.compare_elements(element.id, second_element.id)

        if data[0] == '-':
            second_element = self.database.elements.get_by_id(int(data[10]))
            image = self.database.files.get_by_id(second_element.file_id)
            self.show_non_existing_image(second_element, self.orto_image_a, self.point_cloud_a_file_path)
            self.show_image_internal(second_element, image, 'image_B')
        if data[10] == '-':
            element = self.database.elements.get_by_id(int(data[0]))
            image = self.database.files.get_by_id(element.file_id)
            self.show_image_internal(element, image)
            self.show_non_existing_image(element, self.orto_image_b, self.point_cloud_b_file_path, 'image_B')

        self.point_cloud_viewer.show()

    def show_non_existing_image(self, existing_element, orto_image, point_cloud_file_path, image_str="image_A"):
        cropped_image = orto_image.window_centered(existing_element.lat, existing_element.lon, 800, 800)
        self.show_image_internal(existing_element, cropped_image, image_str=image_str, from_array=True)
        cropped_point_cloud = PointCloudTools.crop(point_cloud_file_path, existing_element.lat, existing_element.lon, existing_element.height, 2)
        if image_str == "image_A":
            self.point_cloud_viewer.compare_point_clouds(self.point_cloud_viewer.get_point_cloud(existing_element), cropped_point_cloud)
        if image_str == "image_B":
            self.point_cloud_viewer.compare_point_clouds(cropped_point_cloud, self.point_cloud_viewer.get_point_cloud(existing_element))

    def show_image_internal(self, element, image, image_str="image_A", from_array=False):
        image_element = getattr(self, image_str)
        if image_element is None:
            if from_array:
                setattr(self, image_str, AdvancedImage(self.container, image_array=image))
            else:
                setattr(self, image_str, AdvancedImage(self.container, image))
            getattr(self, image_str).show({"anchor": "s", "side": "left"})
        else:
            image_element.clear()
            if from_array:
                image_element.replace_from_array(image)
            else:
                if image_element.id != element.file_id:
                    image_element.replace_image(image)
                    image_element.id = element.file_id
        color = 'blue' if (image_str == 'image_A') else 'green1'
        if from_array:
            bbox = np.fromstring(element.bbox[1:-1], dtype="int", count=4, sep=" ")
            width = int((bbox[3] - bbox[1]) / 2)
            height = int((bbox[2] - bbox[0]) / 2)
            points = [400 - height, 400 - width, 400 + height, 400 + width]
            getattr(self, image_str).add_point(element.__dict__, color=color, points=points, width=3)
        else:
            getattr(self, image_str).add_point(element.__dict__, color=color, width=3)
