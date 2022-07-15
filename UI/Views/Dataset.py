from UI.Button import UIButton
from UI.Container import Container
from UI.Table import Header, Table
from UI.Text import Text
from UI.TextInput import TextInput
from UI.Views.View import View


class Dataset(View):
    def __init__(self, root, container, session):
        super(Dataset, self).__init__(root, container, session)

        headers = Header.headers_from_list(
            [
                {"title": "Id", "width": 50},
                ("Title", self.select_dataset, 300),
                "Description",
                {"title": "CreatedOn", "width": 200},
            ]
        )
        self.table = Table(
            container,
            headers,
            delete_method=self.delete_dataset,
            options={"anchor": "nw", "fill": "x"},
        )

        # Create inputs
        self.inputs_container = Container(
            self.container, pack_options={"side": "top", "pady": 5}
        )

        self.description_input = TextInput(
            self.inputs_container.el, "Description")
        # self.type_input = TextInput(
        #     self.inputs_container.el, "Type",
        #     next_element=self.description_input)
        self.title_input = TextInput(
            self.inputs_container.el, "Title", next_element=self.description_input
        )

        # Show inputs
        self.title_input.show()
        # self.type_input.show()
        self.description_input.show()

        # Create buttons
        buttons_container = Container(
            self.inputs_container.el, pack_options={"side": "bottom"}
        )

        button_options = {"pady": 5}
        UIButton(
            buttons_container.el,
            "Add Dataset",
            self.insert,
            width=30).show(button_options)

        self.load()
        self.inputs_container.show()
        buttons_container.show()
        self.text = Text(container)
        self.text.show()

    def clear(self):
        # clear the content of text entry box
        self.title_input.clear()
        # self.type_input.clear()
        self.description_input.clear()

    def select_dataset(self, data):
        self.emit("select", int(data[0]))

    # Function to take data from GUI
    # window and write to database
    def insert(self):
        data = {
            "title": self.title_input.get(),
            "type": 1,
            "description": self.description_input.get(),
        }

        if all(data.values()):
            added_dataset = self.database.datasets.add(data)

            self.load()
            self.clear()
        else:
            self.text.set_value("Please fill all fields")

    def delete_dataset(self, dataset_id):
        self.database.datasets.delete(int(dataset_id))

    def load(self):
        self.table.add_data(
            [
                [d.id, d.title, d.description, d.creation_date]
                for d in self.database.datasets.all()
            ]
        )
        self.table.show()
