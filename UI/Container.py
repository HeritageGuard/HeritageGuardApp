from tkinter import Frame, TOP


class Container:
    def __init__(self, parent, pack_options={"side": TOP}, frame_options={}):
        self.el = Frame(parent, **frame_options)
        self._packOptions = pack_options

    def show(self):
        self.el.pack(self._packOptions)

    def hide(self):
        self.el.pack_forget()

    def destroy(self):
        self.el.destroy()
