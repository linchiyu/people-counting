import json

def readJsonFile(filename='config.json'):
	with open('config.json', 'r') as f:
		datastore = json.load(f)
	return datastore
	

def writeJsonFile(filename='config.json', data={}):
	with open(filename, 'w') as f:
		json.dump(datastore, f)
