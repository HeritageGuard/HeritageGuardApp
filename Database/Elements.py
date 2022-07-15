import gc

import numpy as np
from sqlalchemy.sql import exists

from Database.Database import Element


class Elements:
    def __init__(self, session):
        self._session = session

    def add(self, element, immediate_commit=True):
        element_to_add = Element(
            dataset_id=element["dataset_id"],
            file_id=element["file_id"],
            element_type=element["element_type"],
            lat=element["lat"],
            lon=element["lon"],
            height=element["height"],
            score=element["score"],
            bbox=np.array2string(element["bbox"]),
            address=element["address"],
            status=element["status"],
            name=element["name"],
            code=element["code"]
        )
        self._session.add(element_to_add)
        if immediate_commit:
            self._session.commit()
            element_id = element_to_add.id
            print('Added element wiht id {}'.format(element_to_add.id))

            self._session.expunge(element_to_add)
            self._session.expire_all()
            del element
            del element_to_add
            gc.collect()

            return element_id
        return None

    def get_by_id(self, oid):
        return self._session.query(Element).filter(Element.id == oid).first()

    def get_by_dataset_id(self, oid):
        return self._session.query(Element).filter(Element.dataset_id == oid).all()

    def get_by_file_id(self, oid):
        return self._session.query(Element).filter(Element.file_id == oid).all()

    def any_by_dataset_id(self, oid):
        return self._session.query(exists().where(
            Element.dataset_id == oid)).scalar()

    def delete(self, oid):
        result = self._session.query(Element).filter_by(id=oid).delete()
        self._session.commit()
        return result

    def all(self):
        return self._session.query(Element).all()
