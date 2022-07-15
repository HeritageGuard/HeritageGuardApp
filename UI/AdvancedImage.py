from functools import partial
from tkinter import BOTH, NW, Canvas

import numpy as np
from PIL import Image, ImageTk


class AdvancedImage:
    def __init__(
            self,
            parent,
            image_data=None,
            id=0,
            image_array=None,
            pack_options={"fill": BOTH, "expand": 1},
    ):
        image = None
        if image_data:
            image = self._image_from_db_entry(image_data)
        elif len(image_array) > 0:
            image = Image.fromarray(image_array)
            image.convert("RGB")

        self.id = id

        img = ImageTk.PhotoImage(image)
        self.width = img.width()
        self.height = img.height()

        self._tags = []

        self.canvas = Canvas(parent, width=img.width(), height=img.height())
        self.canvas.create_image(0, 0, anchor=NW, image=img)
        self.canvas.image = img

        self._options = None

    def show(self, options=None):
        if options is None:
            if self._options:
                self.canvas.pack(**self._options)
            else:
                self.canvas.pack()
        else:
            self._options = options
            self.canvas.pack(**options)

    def show_grid(self, row, column):
        self.canvas.grid(row=row, column=column)

    def hide(self):
        self.canvas.pack_forget()

    def destroy(self):
        self.canvas.destroy()

    @staticmethod
    def click(data, method, _):
        method(data)

    def clear(self):
        for tag in self._tags:
            self.canvas.delete(tag)

    def replace_image(self, image):
        img = ImageTk.PhotoImage(self._image_from_db_entry(image))
        self.canvas.create_image(0, 0, anchor=NW, image=img)
        self.canvas.image = img

    def replace_from_array(self, image):
        image = Image.fromarray(image)
        image.convert("RGB")
        img = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor=NW, image=img)
        self.canvas.image = img

    def add_point(self, data, method=None, current=False, color=None, points=None, width=1):
        tag = "test_" + str(data["id"])

        if points is None:
            if isinstance(data["bbox"], str):
                points = np.fromstring(
                    data["bbox"][1:-1], dtype="int", count=4, sep=" ")
            else:
                points = data["bbox"]

        if color is None:
            color = "red"
            if data["score"] > 0.8:
                color = "yellow"
            if data["score"] > 0.95:
                color = "green"
            if current:
                color = "blue"

        if current:
            width = 3

        self._tags.append(tag)

        self.create_rectangle(
            points[1],
            points[0],
            points[3],
            points[2],
            outline=color,
            fill="blue",
            alpha=0,
            tags=tag,
            width=width,
        )
        if method:
            self.canvas.tag_bind(
                tag, "<Button-1>", partial(self.click, data, method))

    def create_rectangle(self, x, y, a, b, **options):
        if "alpha" in options:
            # Calculate the alpha transparency for every color(RGB)
            alpha = int(options.pop("alpha") * 255)
            # Use the fill variable to fill the shape with transparent color
            fill = options.pop("fill")
            fill = self.canvas.winfo_rgb(fill) + (alpha,)
            image = Image.new("RGBA", (a - x, b - y), fill)
            img = ImageTk.PhotoImage(image)
            self.canvas.create_image(
                x, y, image=img, anchor="nw", tags=options["tags"])
            self.canvas.create_rectangle(x, y, a, b, **options)

    @staticmethod
    def _image_from_db_entry(image_from_db):
        return Image.frombytes(
            "RGB", (image_from_db.width,
                    image_from_db.height), image_from_db.content
        )
