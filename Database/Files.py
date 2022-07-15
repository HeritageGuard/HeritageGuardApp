from datetime import datetime

from Database.Database import File


class Files:
    def __init__(self, session):
        self._session = session

    def add(self, file):
        added_file = File(
            filename=file["filename"],
            creation_date=datetime.now(),
            meta=file["meta"],
            content=file["content"],
            dataset_id=file["dataset_id"],
            width=file["width"],
            height=file["height"],
        )
        self._session.add(added_file)
        self._session.commit()

        return added_file.id

    def get_by_id(self, oid):
        return self._session.query(File).filter(File.id == oid).first()

    def get_by_dataset_id(self, oid):
        return self._session.query(File).filter(File.dataset_id == oid)

    def all(self):
        return self._session.query(File).all()
