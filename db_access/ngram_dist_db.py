from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData, Table, Column, String, Integer, create_engine, PrimaryKeyConstraint, or_, and_
from sqlalchemy.orm import mapper, sessionmaker
from models.config import Config
from db_access.sqlite_base import BaseSqliteDb
from enum import Enum
from collections import defaultdict

ObjDistBase = declarative_base()


class ObjDistNGram(ObjDistBase):
    __tablename__ = 'n_gram_dist'
    token_type = Column(String(1))
    token = Column(String(), primary_key=True, sqlite_on_conflict_primary_key='REPLACE')
    value = Column(Integer())


class DistEnum(Enum):
    __order__ = 'uni back_bi fwd_bi tri '
    uni = 'u'
    back_bi = 'b'
    fwd_bi = 'f'
    tri = 't'

    @classmethod
    def get_enum_from_val(cls, val):
        val_to_enum = {
            'u': cls.uni,
            'b': cls.back_bi,
            'f': cls.fwd_bi,
            't': cls.tri
        }
        return val_to_enum.get(val)


class ObjDisEntityFactory:

    def make_entity(self, dist, token, value):
        return ObjDistNGram(token_type=dist, token=token, value=value)


class ObjectDistributionsSQLite(BaseSqliteDb):

    filename = f'{Config.MODEL_DIR}/ngram_distributions.db'
    base = ObjDistBase

    def select(self, dist_type_to_tokens):
        or_filters = []
        for dist_type, tokens in dist_type_to_tokens.items():
            for token in tokens:
                or_filters.append(and_(ObjDistNGram.token == token,
                                       ObjDistNGram.token_type == dist_type.value))
        results = self.session.query(ObjDistNGram).filter(or_(*or_filters))
        rtn = defaultdict(dict)
        for result in results.all():
            rtn[DistEnum.get_enum_from_val(result.token_type)][result.token] = result.value
        return rtn
