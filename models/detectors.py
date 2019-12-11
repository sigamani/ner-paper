import logging
from allennlp.predictors import Predictor
from gender_guesser.detector import Detector as _GenderDetector
from nltk import ngrams
#from cai_logging import get_logger
from db_access.wiki_db import WikiSQLITE

from models.config import Config


#logger = get_logger("detectors")


def clean_logging():
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)


clean_logging()


def _make_entity(name, label, gender=None):
    entity = {
        'name': name,
        'type': label,
    }
    if gender:
        entity["subtype"] = gender
    return entity


class AllenNlpDetector:
    """
    Use AllenNlp to tokenise and detect person/ location entities
    """
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(AllenNlpDetector, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.ent_types = Config.ENTITY_TYPES
        self.predictor = Predictor.from_path(Config.MODEL_PATH)

    @staticmethod
    def _is_contraction(string):
        return len(string.split()) == 1 and not string.isalpha()

    @staticmethod
    def _iterate_results(results):
        for tag, word in zip(results["tags"], results["words"]):
            yield tag, word

    def _is_unigram(self, tag):
        return any([f'U-{label}' == tag for label in self.ent_types])

    @staticmethod
    def _handle_unigram(tag, word):
        #logger.debug("Detected unigram: %s", word)
        return _make_entity(word, tag[2:])

    def _is_ngram(self, tag):
        return any([f'B-{label}' == tag for label in self.ent_types])

    @staticmethod
    def _handle_ngram(tag, word, iterator):
        label = tag[2:]
        words = [word]
        next_tag, next_word = next(iterator)
        while next_tag == f'I-{label}':
            words.append(next_word)
            next_tag, next_word = next(iterator)
        words.append(next_word)
        #logger.debug("Detected n-gram: %s", ' '.join(words))
        return _make_entity(' '.join(words), label)

    def predict(self, message):
        try:
            return self.predictor.predict(sentence=message)
        except RuntimeError:
            #logger.warning("message '%s' unable to be parsed by allennlp", message)
            return {'tags': [], 'words': []}  # null results

    def combine_entities(self, tag):
        conversion_dict = {'U-GPE': 'U-LOC', 'B-GPE': 'B-LOC', 'L-GPE': 'I-LOC'}
        if tag in conversion_dict.keys():
            return conversion_dict[tag]
        else:
            return tag

    def get_entities(self, message):
        results = self.predict(message)
        res_valid, res_others = [], []
        iterator = self._iterate_results(results)
        for tag, word in iterator:
            tag = self.combine_entities(tag)
            if self._is_unigram(tag):
                res_valid.append(self._handle_unigram(tag, word))
            elif self._is_ngram(tag):
                res_valid.append(self._handle_ngram(tag, word, iterator))
            else:
                res_others.append(_make_entity(word, tag))
        return res_valid, res_others


class GenderDetector:
    def __init__(self):
        self.country_list = ['great_britain', 'usa']
        self.detector = _GenderDetector(case_sensitive=False)
        self.weak_genders = ['unknown', 'andy']

    def _ent_checker(self, string, country):
        return self.detector.get_gender(string)

    def find_people(self, entities):
        ents = []
        for entity in entities:
            token = entity["name"]
            gender = self._get_strong_gender(token)
            if gender:
               # logger.debug("Gender match found: %s", token)
                ents.append(_make_entity(token, 'PER', gender))
        return ents

    def _get_strong_gender(self, name):
        for country in self.country_list:
            gender = self._ent_checker(name, country)
          #  if gender not in self.weak_genders:
          #      return gender
        return gender

    def _process_gender(self, entity):
        if entity.get('type') != 'PERSON':
            return entity
        name = entity["name"].split()
        entity["gender"] = self._get_strong_gender(name[0]) or "andy"  # coerce weak to andy
        if entity["gender"] != "unknown":
            return entity

    def get_gender(self, entities):
        return [self._process_gender(entity) for entity in entities]


class WikidataDetector:
    """
    Check entities from AllenNLP with wikidata lookup for subtype
    """

    def __init__(self):
        self.wiki_db = WikiSQLITE.check_and_connect()

    def _check_database(self, ent_name, ent_type):
       # logger.info(f"Checking db for {ent_name} of type {ent_type}")
        subtype = self.wiki_db.select(ent_type, ent_name)
        if subtype is not None:
           # logger.info(f"Subtype for {ent_name} is {subtype}")
            return ent_name, subtype

        ent_name_without_the = ent_name.replace('the ', '')
        subtype_no_the = self.wiki_db.select(ent_type, ent_name_without_the)
        if subtype_no_the is not None:
           # logger.info(f"Subtype for {ent_name} without 'the' is {subtype_no_the}")
            return ent_name_without_the, subtype_no_the

        redirect_result = self.wiki_db.select('redirect', ent_name)
        if redirect_result is not None:
            redirected_subtype = self.wiki_db.select(ent_type, redirect_result)
            if redirected_subtype is not None:
               # logger.info(f"Subtype for {ent_name} after redirect is {redirected_subtype}")
                return redirect_result, redirected_subtype
       # logger.info(f"Subtype for {ent_name} is None")
        return ent_name, ""

    def get_person_subtype(self, name, gender):
        if len(name.split()) == 1:
            """If only one name return gender to avoid """
           # logger.info(f"Returning gender for single name: {name}")
            return name, gender
        ent_name, ent_subtype = self._check_database(name, 'person')
        if not ent_subtype:
           # logger.info(f"Returning gender because no subtype")
            ent_subtype = gender
        return ent_name, ent_subtype

    @classmethod
    def _get_db_type(cls, ent_type):
        if ent_type in ['GPE', 'LOC', 'FAC']:
            return 'location'
        if ent_type == 'ORG':
            return 'organisation'
        if ent_type in ['PRODUCT', 'WORK_OF_ART', 'EVENT']:
            return ent_type.lower()
        return None

    def get_finegrained_result(self, ents):
        results = []

        for ent in ents:
            ent_name = ent.get('name').lower()
            ent_type = ent.get('type')
            ent_subtype = ""

            if ent_type in ['PER', 'PERSON']:
                ent_type = 'person'
                ent_name, ent_subtype = self.get_person_subtype(ent_name, ent.get('gender'))

            db_type = self._get_db_type(ent_type)
            if db_type:
                ent_type = db_type
                ent_name, ent_subtype = self._check_database(ent_name, db_type)

            elif ent_type in ["CARDINAL", "DATE", "MONEY", "ORDINAL", "PERCENT", "QUANTITY", "TIME"]:
                ent_subtype = ent_type.lower()
                ent_type = 'numeric'

            results.append({"name": ent_name, "type": ent_type.lower(), "subtype": ent_subtype})

        return results
