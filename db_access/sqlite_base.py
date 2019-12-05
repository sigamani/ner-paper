import os
from models.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class NoSuchDatabaseError(Exception):
    def __init__(self, db):
        self.db = db

    def __repr__(self):
        return f"Could not find database file {self.db} to read from"


class BaseSqliteDb:

    filename = None
    base = None

    def __init__(self):
        self._connect()

    def _connect(self):
        self.engine = create_engine(f'sqlite:///{self.filename}')
        self.base.metadata.bind = self.engine
        self.session = sessionmaker(bind=self.engine)()

    def insert(self, entry):
        self.session.add(entry)

    def commit(self):
        self.session.commit()

    @classmethod
    def check_and_connect(cls):
        if not os.path.exists(cls.filename):
            raise NoSuchDatabaseError(cls.filename)
        return cls()

    @classmethod
    def new(cls, dbname):
        klass = cls()
        if not klass.engine.dialect.has_table(klass.engine, dbname):
            cls.base.metadata.create_all(klass.engine)
        return klass
