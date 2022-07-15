from tkinter import Frame, Label, Entry, Button, LEFT, RIGHT, END, TOP, NW, BOTH


class TextButton:
    def __init__(self, parent, label_text, button_command, next_element=None):
        self._hidden = None
        self.frame = Frame(parent)
        self.label = Label(self.frame, text=label_text)
        self.el = Entry(self.frame, fg="black", bg="white")
        self.button = Button(
            self.frame,
            text="Choose file",
            fg="white",
            bg="#b19326",
            activebackground="#92791c",
            bd=0,
            command=button_command,
        )
        self._options = None

        if next_element:
            self.next_element = next_element
            self.el.bind("<Return>", self.focus_next)

        self.label.pack(side=LEFT)
        self.button.pack(side=RIGHT, padx=5)
        self.el.pack(side=RIGHT)

    def set(self, text):
        self.el.delete(0, END)
        self.el.insert(0, text)

    def set_hidden(self, text):
        self._hidden = text

    def focus_next(self, event):
        self.next_element.el.focus_set()

    def get(self):
        return self.el.get()

    def get_hidden(self):
        return self._hidden

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
