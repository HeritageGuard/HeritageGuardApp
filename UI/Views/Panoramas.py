from datetime import date
from functools import partial
from pathlib import Path
from tkinter import Canvas, NW
from tkinter.filedialog import askopenfile, asksaveasfilename

import diplib as dip
import numpy as np
from PIL import Image, ImageTk
from cv2 import cvtColor, COLOR_RGB2RGBA, COLOR_BGR2GRAY, THRESH_BINARY_INV, THRESH_BINARY, threshold, subtract, imread, \
    COLOR_GRAY2BGR, THRESH_OTSU, getStructuringElement, MORPH_ELLIPSE, morphologyEx, MORPH_CLOSE, MORPH_DILATE, \
    RETR_EXTERNAL, CHAIN_APPROX_NONE, findContours, drawContours, resize

from UI.Button import UIButton
from UI.Container import Container
from UI.ProgressBar import ProgressBar
from UI.TextButton import TextButton
from UI.TextInput import TextInput
from UI.Views.View import View


class Panoramas(View):
    def __init__(self, root, container, session):
        super(Panoramas, self).__init__(root, container, session)

        self.inputs_container = Container(
            self.container, pack_options={
                "side": "top", "anchor": "n", "pady": 10}
        )

        self.image = None
        self.image_ref = None
        self.file_name = None
        self.result_mode = 1

        all_datasets = self.database.datasets.all()
        menu_options = dict([[d.id, d.title] for d in all_datasets])

        self.file_a = TextButton(
            self.inputs_container.el,
            "Select photo A (.jpg or .png)",
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
        self.file_b = TextButton(
            self.inputs_container.el,
            "Select photo B (.jpg or .png)",
            partial(
                self.open_file,
                1,
                [
                    ("Image File", "*.jpg"),
                    ("Image File", "*.JPG"),
                    ("Image File", "*.png"),
                    ("Image File", "*.PNG"),
                ],
            ),
        )

        self.file_inputs = [self.file_a, self.file_b]

        for file_input in self.file_inputs:
            file_input.show({"side": "left", "anchor": "n"})

        UIButton(self.inputs_container.el, "Compare",
                 self.compare).show({"side": "left", "anchor": "n", "padx": 5})

        self.save_button = UIButton(self.inputs_container.el, "Save", self.save_image)

        self.controls_container = Container(
            self.container, pack_options={
                "side": "top", "anchor": "n", "pady": 10}
        )

        UIButton(self.controls_container.el, "Show A",
                 self.show_a).show({"side": "left", "anchor": "n", "padx": 5})

        UIButton(self.controls_container.el, "Show B",
                 self.show_b).show({"side": "left", "anchor": "n", "padx": 5})

        UIButton(self.controls_container.el, "Show result",
                 self.set_result_mode).show({"side": "left", "anchor": "n", "padx": 5})

        self.filter_size_input = TextInput(self.controls_container.el, "Filter size")
        self.filter_size_input.show({"side": "left", "anchor": "n", "padx": 5})

        self.filter_size_input.set(5000000)

        self.kernel1_size_input = TextInput(self.controls_container.el, "Kernel 1 size")
        self.kernel1_size_input.show({"side": "left", "anchor": "n", "padx": 5})

        self.kernel1_size_input.set(1)

        self.kernel2_size_input = TextInput(self.controls_container.el, "Kernel 2 size")
        self.kernel2_size_input.show({"side": "left", "anchor": "n", "padx": 5})

        self.kernel2_size_input.set(5)

        self.inputs_container.show()
        self.canvas = Canvas(self.container)

    def compare(self):
        self.canvas.pack_forget()
        progress_bar = ProgressBar(
            self.container, self.root, pack_options={"expand": 1, "fill": "x"}
        )
        progress_bar.show()

        progress_bar.set_value(0, 'Opening images')

        fname1 = self.file_a.get_hidden()
        fname2 = self.file_b.get_hidden()
        imageA = imread(fname1)
        imageB = imread(fname2)

        progress_bar.set_value(10, 'Preparing first image')

        imageA = self.prepare_image(imageA)
        progress_bar.set_value(40, 'Preparing second image')
        imageB = self.prepare_image(imageB)
        progress_bar.set_value(60, 'Calculating differences')
        # compute difference
        differenceAB = subtract(imageA, imageB)
        progress_bar.set_value(70, 'Calculating differences')
        differenceBA = subtract(imageB, imageA)
        progress_bar.set_value(80, 'Generating report')

        # color the mask red
        ret, maskAB = threshold(
            differenceAB, 0, 255, THRESH_BINARY_INV | THRESH_BINARY)
        ret, maskBA = threshold(
            differenceBA, 0, 255, THRESH_BINARY_INV | THRESH_BINARY)
        progress_bar.set_value(90, 'Generating report')

        maskAB = cvtColor(maskAB, COLOR_BGR2GRAY)
        maskBA = cvtColor(maskBA, COLOR_BGR2GRAY)

        imageAB = imageA.copy()
        imageAB = cvtColor(imageAB, COLOR_RGB2RGBA)
        imageAB[maskAB != 255] = [0, 255, 0, 170]
        imageAB[maskBA != 255] = [255, 0, 255, 170]

        imageAB[np.where((imageAB == [255, 255, 255, 255]).all(axis=2))] = [0, 0, 0, 0]
        imageAB[np.where((imageAB == [0, 0, 0, 255]).all(axis=2))] = [0, 0, 0, 0]

        progress_bar.set_value(100, 'Done!')

        self.image = Image.fromarray(self.resize(imageAB), 'RGBA')
        progress_bar.destroy()
        self.controls_container.show()
        self.save_button.show({"side": "left", "anchor": "n", "padx": 5})
        self.result_mode = 1
        self.show_a()

    def set_result_mode(self):
        if self.result_mode == 1:
            self.result_mode = 2
        elif self.result_mode == 2:
            self.result_mode = 0
        else:
            self.result_mode = 1
        self.show_image_internal()

    def show_a(self):
        self.file_name = self.file_a.get_hidden()
        self.show_image_internal()

    def show_b(self):
        self.file_name = self.file_b.get_hidden()
        self.show_image_internal()

    def show_image_internal(self):
        if self.image_ref is not None:
            self.canvas.delete(self.image_ref)
            self.canvas.image = None

        image = self.get_image_to_show()
        img = ImageTk.PhotoImage(image)

        self.image_ref = self.canvas.create_image(0, 0, anchor=NW, image=img)

        self.canvas.image = img
        self.canvas.config(width=img.width(), height=img.height())
        self.canvas.pack({"anchor": "s", "side": "left", "expand": True, "fill": "both"})

    def save_image(self):
        file_name = asksaveasfilename(defaultextension=".jpg",
                                      initialfile="report_panoramas_" + date.today().strftime("%Y_%m_%d") + ".jpg")
        if file_name is None:
            return
        image = self.get_image_to_show()
        image.save(file_name)
    def get_image_to_show(self):
        if self.result_mode == 0:
            return self.image
        image = Image.open(self.file_name)
        image = image.resize(self.image.size)
        if self.result_mode == 1:
            image = image.resize(self.image.size)
            fg_img_trans = Image.new("RGBA", self.image.size)
            fg_img_trans = Image.blend(fg_img_trans, self.image, 1.0)
            image.paste(fg_img_trans, (0, 0), fg_img_trans)
        return image

    def prepare_image(self, image):
        h, w, c = image.shape

        image_bgr_grey = cvtColor(image, COLOR_BGR2GRAY)
        # image_bgr_grey = cv2.Laplacian(image_bgr_grey, ddepth, ksize=kernel_size)
        # image_bgr_grey = cv2.convertScaleAbs(image_bgr_grey, alpha=15, beta=0)
        # image_bgr_grey = cv2.GaussianBlur(image_bgr_grey, (3, 3), 0)
        image_bgr_grey = self.fill_in(image_bgr_grey)
        th, image_bgr_grey = threshold(image_bgr_grey, 0, 255, THRESH_OTSU)
        image = cvtColor(image_bgr_grey, COLOR_GRAY2BGR)
        return image

    def fill_in(self, img):
        out = np.zeros_like(img)
        kernel_1_size = int(self.kernel1_size_input.get())
        kernel_2_size = int(self.kernel2_size_input.get())
        kernel1 = getStructuringElement(MORPH_ELLIPSE, (kernel_1_size, kernel_1_size))
        kernel2 = getStructuringElement(MORPH_ELLIPSE, (kernel_2_size, kernel_2_size))
        morph = morphologyEx(img, MORPH_CLOSE, kernel1, iterations=1)
        morph = morphologyEx(morph, MORPH_DILATE, kernel2, iterations=1)
        lines = dip.AreaClosing(dip.Image(morph), filterSize=int(self.filter_size_input.get()))
        res = findContours(np.array(lines), RETR_EXTERNAL, CHAIN_APPROX_NONE)
        contours = res[-2]
        drawContours(out, contours, contourIdx=-1, color=(255, 255, 255), thickness=-1)
        return out

    def open_file(self, index, file_types):
        opened_file = askopenfile(filetypes=file_types)
        if opened_file:
            filePath = opened_file.name
            self.file_inputs[index].set(Path(filePath).name)
            self.file_inputs[index].set_hidden(filePath)

    def resize(self, image, scale=30):
        width = int(image.shape[1] * scale / 100)
        height = int(image.shape[0] * scale / 100)
        dim = (width, height)
        return resize(image, dim)
