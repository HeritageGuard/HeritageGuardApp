from tkinter import StringVar, Label


class Text:
    def __init__(self, parent, value=None, pack_options={}):
        self.value = StringVar()
        self.el = Label(parent, textvariable=self.value)
        self._options = None

        if value:
            self.value.set(value)
        self.el.pack(**pack_options)

    def set_value(self, value):
        self.value.set(value)

    def show(self, options=None):
        if options is None:
            if self._options:
                self.el.pack(**self._options)
            else:
                self.el.pack()
        else:
            self._options = options
            self.el.pack(**options)

    def hide(self):
        self.el.pack_forget()

    def destroy(self):
        self.el.destroy()
