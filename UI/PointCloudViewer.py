from genericpath import exists
import os.path
import zlib
from functools import partial
from tkinter import Scale

import laspy
import numpy as np
from vispy.app import use_app
from vispy.scene import SceneCanvas, visuals

from UI.Button import UIButton
from UI.Container import Container


class PointCloudViewer:
    def __init__(self, parent, database):
        self.database = database
        self.container = Container(
            parent,
            pack_options={
                "side": "left",
                "anchor": "w",
                "fill": "both",
                "expand": True})
        app = use_app('tkinter')
        self.canvas = SceneCanvas(
            'Test', parent=self.container.el, show=True, app=app)
        self.scatter = None
        self.view = None
        buttons_container = Container(
            self.container.el,
            pack_options={
                "side": "top",
                "anchor": "n",
                "expand": False})
        buttons_container.show()
        buttons_show_options = {"anchor": "w", "side": "left"}
        buttons_show_options_with_margin = {
            "anchor": "w", "side": "left", "padx": (10, 0)}
        UIButton(buttons_container.el, "<", partial(
            self.turn, None, None, 20)).show(buttons_show_options)
        UIButton(buttons_container.el, "W", partial(
            self.turn, 270, None, None)).show(buttons_show_options)
        UIButton(buttons_container.el, "N", partial(
            self.turn, 180, None, None)).show(buttons_show_options)
        UIButton(buttons_container.el, "S", partial(
            self.turn, 0, None, None)).show(buttons_show_options)
        UIButton(buttons_container.el, "E", partial(
            self.turn, 90, None, None)).show(buttons_show_options)
        UIButton(buttons_container.el, ">", partial(
            self.turn, None, None, -20)).show(buttons_show_options)

        UIButton(
            buttons_container.el, "T", partial(self.turn, 0, 90, None)).show(
            buttons_show_options_with_margin)
        UIButton(buttons_container.el, "B", partial(
            self.turn, 0, -90, None)).show(buttons_show_options)

        Scale(buttons_container.el, from_=0, to=130,
              orient='horizontal', command=self.set_fov).pack()
        self.zoom_scale = Scale(
            buttons_container.el,
            from_=1,
            to=30,
            orient='horizontal',
            command=self.set_zoom)
        self.zoom_scale.pack()

    def open_point_cloud(self, id):
        element = self.database.elements.get_by_id(id)
        point_cloud_data = self.get_point_cloud(element)
        if len(point_cloud_data) == 0:
            print('No point cloud data')
            return
        pos = self._get_pos(point_cloud_data)

        if self.view is None:
            self.view = self.canvas.central_widget.add_view()

        if self.scatter is None:
            self.scatter = visuals.Markers()
            self.view.add(self.scatter)
        self.scatter.set_data(pos, edge_color=None,
                              face_color=(0, 1, 0, .5), size=5)

        self._update_and_show()

    def compare_elements(self, element_A_id, element_B_id):
        element_A = self.database.elements.get_by_id(element_A_id)
        element_B = self.database.elements.get_by_id(element_B_id)

        element_A_array = self.get_point_cloud(element_A)
        element_B_array = self.get_point_cloud(element_B)

        self.compare_point_clouds(element_A_array, element_B_array)

    def compare_point_clouds(self, element_A_array, element_B_array):
        pos = self._get_pos(element_A_array, element_B_array)

        if len(element_A_array.shape) == 1:
            colors_A = np.array([[0, 0, 1]] * int(len(element_A_array)))
        else:
            colors_A = np.array([[0, 0, 1]] * element_A_array.shape[1])

        if len(element_B_array.shape) == 1:
            colors_B = np.array([[0, 1, 0]] * int(len(element_B_array)))
        else:
            colors_B = np.array([[0, 1, 0]] * element_B_array.shape[1])

        colors=None
        if len(colors_A) > 0 and len(colors_B) > 0:
            colors = np.vstack((colors_A, colors_B))

        if self.view is None:
            self.view = self.canvas.central_widget.add_view()

        if self.scatter is None:
            self.scatter = visuals.Markers()
            self.view.add(self.scatter)
        self.scatter.set_data(pos, edge_color=colors,
                              face_color=None, size=1)

        self._update_and_show()

    def _get_pos(self, points, points_two=None):
        # if len(points.shape) == 1:
        #     points = np.reshape(points, (3, -1))
        if points_two is not None:
            if len(points.shape) == 1 and len(points_two.shape) == 1:
                x = self.normalize(np.concatenate((points_two['X'] / 100, points['X'] / 100)))
                y = self.normalize(np.concatenate((points_two['Y'] / 100, points['Y'] / 100)))
                z = self.normalize(np.concatenate((points_two['Z'] / 100, points['Z'] / 100)))
            elif len(points.shape) == 1:
                x = self.normalize(np.concatenate((points_two[0], points['X'] / 100)))
                y = self.normalize(np.concatenate((points_two[1], points['Y'] / 100)))
                z = self.normalize(np.concatenate((points_two[2], points['Z'] / 100)))
            elif len(points_two.shape) == 1:
                x = self.normalize(np.concatenate((points_two['X'] / 100, points[0])))
                y = self.normalize(np.concatenate((points_two['Y'] / 100, points[1])))
                z = self.normalize(np.concatenate((points_two['Z'] / 100, points[2])))
        else:
            x = self.normalize(points['X'] / 100)
            y = self.normalize(points['Y'] / 100)
            z = self.normalize(points['Z'] / 100)

        return np.rot90(np.array([x, y, z]))

    def _update_and_show(self):
        # self.scatter.set_gl_state('translucent', blend=True, depth_test=True)
        # self.scatter.set_gl_state(blend=True, blend_func=('src_alpha', 'one_minus_src_alpha'))
        self.scatter.set_gl_state(blend=True, depth_test=True, polygon_offset_fill=False)
        self.view.camera = 'turntable'
        self.view.camera.center = [0, 0, 0]
        self.view.camera.fov = 0

        self.zoom_scale.set(self.view.camera.scale_factor)

        self.canvas.update()
        self.canvas.show()

    @staticmethod
    def get_point_cloud(element):
        file_name = os.path.abspath('./data/' + str(element.dataset_id) + '/' + str(element.id) + '.las')
        data = laspy.read(file_name)
        return data.points.array

    @staticmethod
    def normalize(arr):
        # return arr
        diff = np.amax(np.abs(arr)) - np.amin(np.abs(arr))
        sub = np.amin(np.abs(arr)) + (diff / 2)
        return arr - sub

    def turn(self, azimuth, elevation, azimuth_add):
        if azimuth:
            self.view.camera.azimuth = azimuth
        if elevation:
            self.view.camera.elevation = elevation
        if azimuth_add:
            self.view.camera.azimuth += azimuth_add

    def set_fov(self, fov):
        self.view.camera.fov = fov

    def set_zoom(self, zoom):
        self.view.camera.scale_factor = zoom

    def show(self, options=None):
        self.canvas.native.pack(fill="both", expand=True,
                                anchor="w", side="left")
        self.canvas.update()
        self.container.show()

    def hide(self):
        self.container.hide()
