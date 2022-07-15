from tkinter import Label, BOTH

from PIL import ImageTk, Image


class UIImage:
    def __init__(
            self,
            parent,
            image_location,
            width,
            height,
            pack_options={"fill": BOTH, "expand": 1},
    ):
        img = Image.open(image_location)
        if width and height:
            img = img.resize((width, height), Image.ANTIALIAS)
        img = ImageTk.PhotoImage(img)
        self.panel = Label(parent, image=img)
        self.panel.image = img

        self._options = pack_options

    def show(self, options=None):
        if options is None:
            if self._options:
                self.panel.pack(**self._options)
            else:
                self.panel.pack()
        else:
            self._options = options
            self.panel.pack(**options)

    def hide(self):
        self.panel.pack_forget()
