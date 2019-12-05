import pickle
import sys
import time
import pandas as pd
import os
import pickle

cwd = os.getcwd()
from models.entity_detector import EntityDetector
ent_detector = EntityDetector()


def run():
	while True:
		try:
			sys.stdout.write('>>')
			message = input()
			if message:
				start_time = time.time()
				ents = ent_detector.get_entities(message)
				end_time = time.time()
				print('outcome_ents: ', ents, '| time: ', end_time - start_time)
			else:
				print('No input')
			sys.stdout.flush()
		except KeyboardInterrupt:
			break

def run_on_messages2(messages):
	entity_analysis = dict()
	for c, m in enumerate(messages):
		print(f'processed {c/len(messages)}%')
		try:
			ents = ent_detector.get_entities(m)
			entity_data = []
			for e in ents:
				name, e_type, subtype = e['name'], e['type'], e['subtype']
				entity_data.append((name, e_type, subtype))	
			entity_analysis[m] = entity_data
		except:
			print('did not work')
			continue
	write_to_pickle(entity_analysis)


def run_on_messages(messages):
    for m in messages:
        try:
            ents = ent_detector.get_entities(m)
            print(f"{m} | {ents}")
        except:
            pass

def get_data():
    dir = 'messages.csv'
    data = pd.read_csv(dir, sep='|')
    messages = data['anonymised_messages'].tolist()
    return messages


def get_data_tuple():

    dir = 'data/'

    for f in files:
        data = pickle.load(open(dir+f,"rb"))

    return 


def write_to_pickle(a):
	with open('entity_data.pickle', 'wb') as handle:
		pickle.dump(a, handle, protocol=pickle.HIGHEST_PROTOCOL)


def analyse_data():
	with open(cwd + '/entity_data.pickle', 'rb') as f: data = pickle.load(f)
	to_csv, calculate_metrics = False, True
	
	if to_csv:
		dataset = []
		for k, v in data.items(): dataset.append([str(k), str(v)])
		dataframe = pd.DataFrame(dataset, columns=['message', 'entities'])
		dataframe.to_csv(cwd + '/ner_data.csv', index=False, sep='|')
	
	if calculate_metrics:
		metrics = dict()
		for msg, ents in data.items():
			for e in ents:
				entity = e[2]
				if entity in metrics:
					count = metrics[entity]
					new_count = count + 1 
					metrics[entity] = new_count
				else:
					metrics[entity] = 1 
		
		dataframe = pd.DataFrame.from_dict(metrics, orient='index')
		dataframe.to_csv(cwd + '/detected_subtypes.csv') 	

if __name__ == "__main__": 
    run()
