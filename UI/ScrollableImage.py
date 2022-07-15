from datetime import date
from functools import partial
from io import BytesIO
from tkinter import Frame, BOTH, Scrollbar, Canvas
from tkinter.filedialog import asksaveasfilename

import rasterio
from PIL import Image, ImageTk
from PIL.ImageDraw import ImageDraw


class ScrollableImage(Frame):
    def __init__(self, container=None, pack_options=None, **kw):
        sw = kw.pop('scrollbarwidth', 10)
        image_a_path = kw.pop('image_a_path', None)
        image_b_path = kw.pop('image_b_path', None)
        self.root = kw.pop('root', None)
        super(ScrollableImage, self).__init__(master=container)

        self.canvas = Canvas(self, highlightthickness=0, **kw)

        self.image_ref = None
        Image.MAX_IMAGE_PIXELS = 933120000
        self.image_a = Image.open(image_a_path)
        self.image_b = Image.open(image_b_path)
        self.image_a_tk = ImageTk.PhotoImage(self.image_a)
        self.image_b_tk = ImageTk.PhotoImage(self.image_b)
        self.polygon_dictionary = {}
        self.deleted_polygons = []

        self.show_image(True)

        # Vertical and Horizontal scrollbars
        self.v_scroll = Scrollbar(self, orient='vertical', width=sw)
        self.h_scroll = Scrollbar(self, orient='horizontal', width=sw)
        # Grid and configure weight.
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        # Set the scrollbars to the canvas
        self.canvas.config(xscrollcommand=self.h_scroll.set,
                           yscrollcommand=self.v_scroll.set)
        self.canvas.update()
        # Set canvas view to the scrollbars
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)
        # Assign the region to be scrolled
        self.canvas.config(scrollregion=self.canvas.bbox('all'))
        self.canvas.bind("<Enter>", self._bound_to_mousewheel)
        self.canvas.bind("<Leave>", self._unbound_to_mousewheel)
        self.h_scroll.grid(row=1, column=0, sticky='ew')
        self.v_scroll.grid(row=0, column=1, sticky='ns')
        self.canvas.grid(row=0, column=0, sticky='nsew')

        if pack_options is not None:
            self.options = pack_options
        else:
            self.options = {"fill": BOTH, "expand": 1}

    def show(self, options=None):
        if options is None:
            if self.options:
                self.pack(**self.options)
            else:
                self.pack()
        else:
            self.options = options
            self.pack(**options)

    def hide(self):
        self.pack_forget()

    def add_polygons(self, polygons, orto_photo_path):
        raster = rasterio.open(orto_photo_path, crs="epsg:3346")
        self.polygon_dictionary = {}
        for index, polygon in enumerate(polygons):
            tag = 'poly_' + str(index)
            points = [raster.index(x[0], x[1])[::-1] for x in polygon.points]
            self._add_polygon(tag, points)

    def _add_polygon(self, tag, points):
        self.polygon_dictionary.update({tag: points})
        self.canvas.create_polygon(points, fill='#00ff00',  outline='#00ff00', tag=tag, stipple='gray25')
        self.canvas.tag_bind(tag, '<Control-ButtonPress-1>', partial(self.delete_poly, tag), add=False)

    def _bound_to_mousewheel(self, event):
        self.canvas.bind("<ButtonPress-1>", self.scroll_start)
        self.canvas.bind("<B1-Motion>", self.scroll_move)
        if self.root is not None:
            self.root.bind("<Control-z>", self.undo)

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<B1-Motion>")
        if self.root is not None:
            self.root.unbind("<Control-z>")

    def show_image(self, image_A=True):
        if self.image_ref is not None:
            self.canvas.delete(self.image_ref)
            self.canvas.image = None

        tk_image = self.image_a_tk if image_A else self.image_b_tk
        self.image_ref = self.canvas.create_image(0, 0, anchor='nw', image=tk_image)
        self.canvas.image = tk_image
        self.canvas.lower(self.image_ref)

    def scroll_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def scroll_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def delete_poly(self, tag, event):
        self.canvas.delete(tag)
        self.deleted_polygons.append((tag, self.polygon_dictionary.pop(tag)))

    def undo(self, event):
        if len(self.deleted_polygons) > 0:
            tag, points = self.deleted_polygons.pop()
            self._add_polygon(tag, points)

    def save(self, save_image_a=True):
        image = self.image_a if save_image_a else self.image_b
        file_name = asksaveasfilename(defaultextension=".jpg",
                              initialfile="report_" + date.today().strftime("%Y_%m_%d") + ".jpg")
        if file_name is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            return

        draw = ImageDraw(image, 'RGBA')

        for poly in self.polygon_dictionary.values():
            draw.polygon(poly, fill='#00ff0080', outline='#00ff00')

        image.save(file_name)
