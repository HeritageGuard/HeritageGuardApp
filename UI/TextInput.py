from tkinter import Frame, Label, Entry, LEFT, RIGHT, END, TOP, NW, BOTH


class TextInput:
    def __init__(
            self,
            parent,
            label_text,
            next_element=None,
    ):
        self.frame = Frame(parent)
        self.label = Label(self.frame, text=label_text)
        self.el = Entry(self.frame, fg="black", bg="white")
        self._options = None

        if next_element:
            self.next_element = next_element
            self.el.bind("<Return>", self.focus_next)

        self.label.pack(side=LEFT)
        self.el.pack(side=RIGHT)

    def focus_next(self, event):
        self.next_element.el.focus_set()

    def set(self, text):
        self.el.delete(0, END)
        self.el.insert(0, text)

    def get(self):
        return self.el.get()

    def clear(self):
        self.el.delete(0, END)

    def show(self, options={"side": TOP, "ipady": 5,
                            "anchor": NW, "fill": BOTH}):
        if options is None:
            if self._options:
                self.frame.pack(**self._options)
            else:
                self.frame.pack()
        else:
            self._options = options
            self.frame.pack(**options)

    def hide(self):
        self.frame.pack_forget()
