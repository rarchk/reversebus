import redis;
import pickle;
import json; 
import xmltodict;
import time; 

def toJson(response,__type__):
	toDict = dict();
	if __type__ == "xml":
		toDict = xmltodict.parse(response);
	elif __type__ == "dict":
		toDict = response;
	response = json.dumps(toDict,sort_keys = True, indent = 4, separators = (",",":") );		
	return [response,toDict];				

def get_route(pool,route,timeout):
	conn = redis.Redis(connection_pool=pool)
	pickledDict = conn.get(route);
	if pickledDict == None:
		return -1;
	else:
		resp = pickle.loads(pickledDict);
		if (time.time() - resp["createdAt"] < timeout):
			return -1;
		else:
			return resp["data"];		

def set_route(pool,route,dictResponse):
	conn = redis.Redis(connection_pool=pool)
	resp = {"data":dictResponse,"createdAt":time.time()}
	pickle_dict = pickle.dumps(resp);
	conn.set(route,pickle_dict);

def reset():
	conn = redis.Redis(connection_pool=pool)
	for i in conn.keys():
		conn.delete(i); 	