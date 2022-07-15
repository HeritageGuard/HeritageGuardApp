from tkinter import Button


class UIButton:
    def __init__(self, parent, text, command, height=2, width=None):
        self.el = Button(
            parent,
            text=text,
            command=command,
            fg="white",
            bg="#b19326",
            activebackground="#92791c",
            bd=0,
            width=width,
        )
        self.el.configure(height=height)
        self._options = None

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
