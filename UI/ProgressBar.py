from tkinter.ttk import Progressbar

from UI.Container import Container
from UI.Text import Text


class ProgressBar:
    def __init__(self, parent, root, length=100, pack_options={
        "side": "top"}, frame_options={}):
        self.root = root
        self.container = Container(parent, pack_options, frame_options)
        self.text = Text(self.container.el, 'TEST')
        self.text.show({'side': 'top', 'pady': 5})
        self.el = Progressbar(
            self.container.el,
            orient="horizontal",
            length=length,
            mode="determinate",
            **frame_options
        )
        self.el.pack({'side': 'top', "expand": 1, "fill": "x"})
        self._packOptions = pack_options

    def show(self):
        self.container.show()

    def set_value(self, value, text=''):
        self.root.update_idletasks()
        self.text.set_value(text)
        self.el["value"] = value
        self.root.update_idletasks()

    def set_length(self, value):
        self.el.configure(length=value)

    def hide(self):
        self.el.pack_forget()

    def destroy(self):
        self.el.destroy()
        self.text.destroy()
        self.container.destroy()
