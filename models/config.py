import os
from pathlib import Path


class Config:

    NER_ARCHIVE_NAME = 'https://s3-us-west-2.amazonaws.com/allennlp/models/fine-grained-ner-model-elmo-2018.12.21.tar.gz'
    MODEL_DIR = Path.cwd() / "data/" 
    MODEL_ARCHIVE_PATH = MODEL_DIR / "allennlp.tar.gz"
    MODEL_PATH = "allennlp-model"
    TIME_LIMIT = int(os.getenv("TASK_TIME_LIMIT", "4"))
    ENTITY_TYPES = ['PERSON', 'ORG', 'LOC', 'GPE', 'CARDINAL',
                    'MONEY', 'PRODUCT', 'DATE', 'TIME', 'WORK_OF_ART',
                    'QUANTITY', 'ORDINAL', 'FAC', 'NORP', 'LANGUAGE']
