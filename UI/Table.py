from functools import partial

from tksheet import Sheet


class Table:
    def __init__(
            self,
            parent,
            headers=[],
            show_scrollbars=True,
            show_row_index=True,
            delete_method=None,
            options=None,
    ):
        self.last_row = 0
        self._options = options
        self.headers = headers
        self.rows = []
        self.delete_method = delete_method

        self.table = Sheet(
            parent,
            show_row_index=show_row_index,
            show_x_scrollbar=show_scrollbars,
            show_y_scrollbar=show_scrollbars,
            empty_horizontal=0,
            empty_vertical=0,
            frame_bg="#000",
            top_left_bg="#000",
            table_bg="#000",
            table_fg="#c4c4c4",
            header_bg="#b19326",
            header_selected_cells_bg="#92791c",
            header_fg="white",
            index_bg="#000",
            index_fg="white",
        )
        self.table.enable_bindings(
            [
                "copy",
                "single_select",
                "column_width_resize",
                "right_click_popup_menu",
                "arrowkeys",
                "row_select",
                "column_select"
            ]
        )
        self.table.extra_bindings([("cell_select", self._cell_click)])

        if callable(delete_method):
            self.table.popup_menu_add_command(
                "Delete", self._delete_row, table_menu=False, header_menu=False
            )

        if len(headers) > 0:
            self.table.headers(newheaders=[h.title for h in headers])
            self.table.popup_menu_add_command("Sort Asc", self.sort_by_header, table_menu=False, index_menu=False)
            self.table.popup_menu_add_command("Sort Desc", partial(self.sort_by_header, True), table_menu=False,
                                              index_menu=False)

        self.table.set_column_widths([h.width for h in headers])

    def add_data(self, data):
        self.table.set_sheet_data(data=data, reset_col_positions=False)

    def find_by_id(self, id):
        id_header_index = self._get_id_header()
        if id_header_index is not None:
            row_index = self.table.get_column_data(
                id_header_index).index(str(id))
            self.table.select_cell(row_index, id_header_index)
            self.table.see(row_index, id_header_index)
            self.table.dehighlight_all()
            self.table.highlight_rows(
                [row_index], bg="white", fg="black", redraw=True)

    def sort_by_header(self, reverse=False):
        column = self.table.get_selected_columns().pop()
        data = self.table.get_sheet_data()
        data.sort(key=lambda row: row[column], reverse=reverse)
        self.add_data(data)

    def add_menu_action(self, label, method):
        self.table.popup_menu_add_command(
            label, partial(self._call_row_method, method), header_menu=False, index_menu=False
        )

    def show(self, options=None):
        if options is None:
            if self._options:
                self.table.pack(**self._options)
            else:
                self.table.pack()
        else:
            self._options = options
            self.table.pack(**options)

    def hide(self):
        self.table.pack_forget()

    def _call_row_method(self, method):
        row_index = self.table.get_currently_selected()[0]
        row_data = self.table.get_row_data(row_index)
        id_header_index = self._get_id_header()
        if id_header_index is not None:
            method(row_data[id_header_index], row_data, row_index)

    def _delete_row(self):
        row_index = self.table.get_currently_selected()[1]
        row_data = self.table.get_row_data(row_index)
        id_header_index = self._get_id_header()
        if id_header_index is not None:
            self.delete_method(row_data[id_header_index])
            self.table.delete_row(row_index, deselect_all=True)

    def _cell_click(self, event):
        self.table.dehighlight_all()
        self.table.highlight_rows(
            [event[1]], bg="white", fg="black", redraw=True)
        if callable(self.headers[event[2]].method):
            self.headers[event[2]].method(self.table.get_row_data(event[1]))

    def _get_id_header(self):
        try:
            return [x.title for x in self.headers].index("Id")
        except ValueError:
            return None


class Header:
    def __init__(self, title, method=None, width=190):
        self.title = title
        self.method = method
        self.width = width

    @staticmethod
    def headers_from_list(list_of_headers):
        headers = []
        for item in list_of_headers:
            if isinstance(item, str):
                headers.append(Header(item))
            if isinstance(item, tuple):
                headers.append(Header(item[0], item[1], item[2]))
            if isinstance(item, dict):
                headers.append(
                    Header(
                        item["title"], item.get(
                            "method", None), item.get("width", 190)
                    )
                )
        return headers
