import sys;
import json;
import xmltodict; 
import logging;

''' Loads a json based configuration file into dict '''
def loadConfig(path):
	try:
		with open(path,'r') as f:
			configDict = json.loads( f.read() );
	except Exception as e:
		print ("Bad configuration file name %s %s" % (path,e));
		sys.exit(-1);		
	return configDict;

'''Sets a log format and defines log handleling'''
def initLogger(logger,configDict):
	logger.setLevel(logging.INFO)	

	fh = logging.FileHandler(configDict['log']);
	formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s');
	fh.setFormatter(formatter);

	logger.addHandler(fh);    

def toJson(response,__type__):
	toDict = dict();
	if __type__ == "xml":
		toDict = xmltodict.parse(response);
	elif __type__ == "dict":
		toDict = response;
	response = json.dumps(toDict,sort_keys = True, indent = 4, separators = (",",":") );		
	return [response,toDict];				
