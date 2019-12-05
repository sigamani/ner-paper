# Fine-grained NER

Based off method in paper here: https://arxiv.org/abs/1904.10503 

## Setup 

1) Download AllenNLP model [here](https://drive.google.com/open?id=10_T5MfgmDLlPqJQ_l3nx-wdnpnYUGvmd) 
and wikidata db [here](https://drive.google.com/open?id=1PrGDBHT4qNLtJpk_2M6-fUZi8ycyf1xn) 

2) Decompress model files in ROOTDIR: `tar -xvf data.tar.gz; tar -xvf allennnlp-model.tar.gz` 

3) In a conda environment or otherwise: `pip install -r requirements.txt`

4) To run: `python run_ner.py` 

