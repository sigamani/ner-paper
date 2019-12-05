from cai_logging import get_logger

from models.detectors import AllenNlpDetector, GenderDetector, WikidataDetector
from models.truecaser import TrueCaser


logger = get_logger("cai-ner")


class _EntityDetector:
    entity_detector = None

    def __new__(cls, *args, **kwargs):
        if cls.entity_detector is None:
            cls.entity_detector = super().__new__(cls, *args, **kwargs)
        return cls.entity_detector

    def __init__(self):
        """
        Create detector comprised of sub-detectors
        """

        self.allennlp_detector = AllenNlpDetector()
        self.gender_detector = GenderDetector()
        self.wikidata_detector = WikidataDetector()
        self.truecaser = TrueCaser()

    def get_entities(self, message):
        """
        Find all relevant entities in `message`.
        1. Use truecaser to deal with lower cased text
        2. Use allenNLP to get tokens.
        3. Augment search with gender detection (only for 1 token PERSONs)
        4. Augment search with fine-grained subtypes
        """
        logger.info("Starting NER detection")
        message = self.truecaser.get_result(message)
        logger.debug(f"True cased message: {message}")
        target_entities, _ = self.allennlp_detector.get_entities(message)
        res_tmp = self.gender_detector.get_gender(target_entities)
        res = self.wikidata_detector.get_finegrained_result(res_tmp)
        for i, ent in enumerate(res):
            ent['name'] = res_tmp[i]['name']
        logger.info(f"Fine Grained Results: {res}")
        return res


class EntityDetector:

    def __init__(self):
        self._model = None

    def load(self):
        logger.info("Loading model")
        self._model = _EntityDetector()
        logger.info("Model loaded")

    @property
    def is_loaded(self):
        return self._model is not None

    def get_entities(self, message):
        if self._model is None:
            self._model = _EntityDetector()
        return self._model.get_entities(message)
