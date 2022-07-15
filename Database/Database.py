from sqlalchemy import (
    BLOB,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from constants import *

Base = declarative_base()


class Database:
    def __init__(self):
        self.Engine = create_engine("sqlite:///hg_db.db")
        Base.metadata.create_all(self.Engine)
        Session = sessionmaker(bind=self.Engine)
        self.Session = Session()

    def close(self):
        self.Engine.dispose()


class Dataset(Base):
    __tablename__ = DATASETS_TABLE

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    creation_date = Column(DateTime)
    dataset_type = Column(Integer)
    description = Column(String)
    orto_photo_path = Column(String, nullable=True)
    height_map_path = Column(String, nullable=True)
    point_cloud_path = Column(String, nullable=True)

    files = relationship("File")
    elements = relationship("Element")


class File(Base):
    __tablename__ = FILES_TABLE

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String)
    creation_date = Column(DateTime)
    meta = Column(String)
    content = Column(BLOB)
    dataset_id = Column(Integer, ForeignKey("dataset.id"))
    width = Column(Integer)
    height = Column(Integer)

    elements = relationship("Element")


class Element(Base):
    __tablename__ = ELEMENTS_TABLE

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("dataset.id"))
    file_id = Column(Integer, ForeignKey("file.id"))
    element_type = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    height = Column(Float)
    score = Column(Float)
    bbox = Column(String)
    address = Column(String)
    status = Column(String)
    name = Column(String)
    code = Column(Integer, nullable=True)
