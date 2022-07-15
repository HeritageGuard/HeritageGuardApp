from Database.Datasets import Datasets
from Database.Elements import Elements
from Database.Files import Files


class DatabaseProvider:
    def __init__(self, session):
        self._session = session
        self.datasets = Datasets(session)
        self.files = Files(session)
        self.elements = Elements(session)

    def commit(self):
        # self._session.flush()
        self._session.commit()
        self._session.expunge_all()
        self._session.expire_all()
        self._session.close()
