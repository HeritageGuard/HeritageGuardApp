from datetime import datetime

from Database.Database import Dataset


class Datasets:
    def __init__(self, session):
        self._session = session

    def add(self, dataset):
        entity = Dataset(
            title=dataset["title"],
            creation_date=datetime.now(),
            dataset_type=dataset["type"],
            description=dataset["description"],
        )
        self._session.add(entity)
        self._session.commit()
        self._session.refresh(entity)
        return entity

    def get_by_id(self, oid):
        return self._session.query(Dataset).filter(Dataset.id == oid).first()

    def get_by_title(self, title):
        return self._session.query(Dataset).filter(
            Dataset.title == title).first()

    def all(self):
        return self._session.query(Dataset).all()

    def delete(self, oid):
        result = self._session.query(Dataset).filter_by(id=oid).delete()
        self._session.commit()
        return result
