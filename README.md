# Fine-grained NER

Based off method in paper here: https://arxiv.org/abs/1904.10503 

## Setup 

1) Download AllenNLP model [here](https://drive.google.com/file/d/1--ilbokKI4gDISibhgsbMs-HxkulvzSS/view?usp=sharing) 
and wikidata db [here](https://drive.google.com/file/d/1w7BpZW27as9eXT-WnDfVhRyxYOMg616p/view?usp=sharing) 

2) Decompress model files in ROOTDIR: `tar -xvf data.tar.gz; tar -xvf allennnlp-model.tar.gz` 

3) In a conda environment or otherwise: `pip install -r requirements.txt`

4) To run: `python run_ner.py` 

