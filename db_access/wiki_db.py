import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData, Table, Column, String, Float, create_engine, PrimaryKeyConstraint
from sqlalchemy.orm import mapper, sessionmaker

from db_access.sqlite_base import BaseSqliteDb
from models.config import Config
#from cai_logging import get_logger

#logger = get_logger("wiki-db")

WikiBase = declarative_base()


class WikiPerson(WikiBase):
    __tablename__ = 'people'
    name = Column(String(50), primary_key=True, sqlite_on_conflict_primary_key='REPLACE')
    subtype = Column(String(50))


class WikiWorkOfArt(WikiBase):
    __tablename__ = 'works_of_art'
    name = Column(String(50), primary_key=True, sqlite_on_conflict_primary_key='REPLACE')
    subtype = Column(String(50))


class WikiProduct(WikiBase):
    __tablename__ = 'products'
    name = Column(String(50), primary_key=True, sqlite_on_conflict_primary_key='REPLACE')
    subtype = Column(String(50))


class WikiLocation(WikiBase):
    __tablename__ = 'locations'
    name = Column(String(50), primary_key=True, sqlite_on_conflict_primary_key='REPLACE')
    subtype = Column(String(50))


class WikiOrganisation(WikiBase):
    __tablename__ = 'organisations'
    name = Column(String(50), primary_key=True, sqlite_on_conflict_primary_key='REPLACE')
    subtype = Column(String(50))


class WikiEvent(WikiBase):
    __tablename__ = 'events'
    name = Column(String(50), primary_key=True, sqlite_on_conflict_primary_key='REPLACE')
    subtype = Column(String(50))


class WikiRedirect(WikiBase):
    __tablename__ = 'redirects'
    name = Column(String(50), primary_key=True, sqlite_on_conflict_primary_key='REPLACE')
    subtype = Column(String(50))


type_to_table_class = {
    'person': WikiPerson,
    'location': WikiLocation,
    'redirect': WikiRedirect,
    'work_of_art': WikiWorkOfArt,
    'organisation': WikiOrganisation,
    'product': WikiProduct,
    'event': WikiEvent
}


class WikiEntityFactory:

    @classmethod
    def _get_db_type(cls, ent_type):
        if ent_type in ['PER', 'PERSON']:
            return 'person'
        if ent_type in ['GPE', 'LOC', 'FAC']:
            return 'location'
        if ent_type == 'ORG':
            return 'organisation'
        return ent_type.lower()

    def make_entity(self, ent_name, ent_type, ent_subtype):
        normalised_type = self._get_db_type(ent_type)
        table_for_entry = type_to_table_class[normalised_type]
        if table_for_entry:
            return table_for_entry(name=ent_name, subtype=ent_subtype)
        return None


class WikiSQLITE(BaseSqliteDb):

    filename = f'{Config.MODEL_DIR}/wikidata.db'
    base = WikiBase

    def get_subtypes_for_table(self, table):
        subtypes = []
        results = self.session.query(table.subtype).distinct()
        for result in results:
            subtypes.append(result[0])
        return subtypes

    def remove_old_file_at_path(self, path):
        if os.path.exists(path):
            os.remove(path)

    def write_table_data_to_file(self, table_name, table, file_obj):
        if table_name == 'redirect':
            return
        file_obj.write(f'{table_name}')
        subtypes = self.get_subtypes_for_table(table)
        for subtype in subtypes:
            file_obj.write(f', {subtype}')
        file_obj.write('\n')

    def export_subtypes_to_file(self):
        path = f"{Config.MODEL_DIR}/wiki_subtypes.csv"
        self.remove_old_file_at_path(path)
        with open(path, 'w') as f:
            for table_name, table in type_to_table_class.items():
                self.write_table_data_to_file(table_name, table, f)

    def select(self, ent_type, name):
        result = None
        #logger.info(f"Creating query for {name} in type {ent_type}")
        type_table = type_to_table_class[ent_type]
        if type_table is not None:
            result = self.session.query(type_table).filter(type_table.name == name)
         #   logger.info(f"Query: {result}")
            result = result.one_or_none()
        if result:
            return result.subtype
        #logger.info("No subtype found in wikidb")
        return None
