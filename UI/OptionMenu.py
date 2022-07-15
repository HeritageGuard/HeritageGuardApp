from tkinter import Menubutton, Widget, Menu, TclError, StringVar


class OptionMenu(Menubutton):
    def __init__(self, master, variable, values, **kwargs):
        kw = {
            "borderwidth": 2,
            "textvariable": variable,
            "indicatoron": 1,
            "anchor": "nw",
            "highlightthickness": 0,
            "width": 20,
            "fg": "white",
        }
        super(Widget, self).__init__(master, "menubutton", kw)
        self.widgetName = "tk_optionMenu"
        menu = self.__menu = Menu(self, name="menu", tearoff=0, fg="white")
        self.menuname = menu._w
        # 'command' is the only supported keyword
        callback = kwargs.get("command")
        if "command" in kwargs:
            del kwargs["command"]
        if kwargs:
            raise TclError("unknown option -" + kwargs.keys()[0])
        # Issues with the variables clashing,
        # I personally just depend on the variable's value so it was easiest
        # just to remove this unneeded portion (for my case)
        # menu.add_command(label=value,
        #         command=_setit(variable, value, callback))
        for v in values.keys():  # Change this line to handle dict instead of list
            # Change this line to set to the String value in the dict
            menu.add_command(
                label=values[v], command=_setit(variable, v, callback))
        self["menu"] = menu

    def __getitem__(self, name):  # No changes
        if name == "menu":
            return self.__menu
        return Widget.__getitem__(self, name)

    def destroy(self):  # No changes
        """Destroy this widget and the associated menu."""
        Menubutton.destroy(self)
        self.__menu = None

    # No changes from tkinter's implementation here, I just like it to be
    # available.


class _setit:
    """Internal class. It wraps the command in the widget OptionMenu."""

    def __init__(self, var, value, callback=None):
        self.__value = value
        self.__var = var
        self.__callback = callback

    def __call__(self, *args):
        self.__var.set(self.__value)
        if self.__callback:
            self.__callback(self.__value, *args)


class DictVar(StringVar):
    """Takes a dictionary of int to strings. default 'get' function
        will return strings as normal, but there is also special function for
        returning based on the integer values 'get_int'.
    Setting the variable requires using the integer value set in int_string_dict"""

    def __init__(self, master=None, int_string_dict=None,
                 value=None, name=None):
        StringVar.__init__(self, master, value, name)
        self.__int_string_dict = int_string_dict
        self.__current_int_value = 0

    def get_int(self):
        """Return value of variable as integer."""
        return self.__current_int_value

    def set(self, value):
        """Set the variable to VALUE."""
        string_value = self.__int_string_dict[value]
        self.__current_int_value = value
        super().set(string_value)
