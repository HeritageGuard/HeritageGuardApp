from Database.DatabaseProvider import DatabaseProvider


class View:
    def __init__(self, root, container, session):
        self.root = root
        self.database = DatabaseProvider(session)
        self.container = container
        self.listeners = {}

    def on(self, event, method):
        self.listeners[event] = method

    def emit(self, event, *args, **kwargs):
        if callable(self.listeners[event]):
            self.listeners[event](*args, **kwargs)

    def off(self, event):
        del self.listeners[event]
