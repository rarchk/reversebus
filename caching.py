import redis;
import pickle;
import time; 

def init(configDict):
	pool = redis.ConnectionPool(host='localhost', port=configDict['redis_port'], db=0);
	return pool; 
 

def get_route(pool,route,timeout):
	conn = redis.Redis(connection_pool=pool)
	pickledDict = conn.get(route);
	if pickledDict == None:
		return -1;
	else:
		resp = pickle.loads(pickledDict);
		if (time.time() - resp["createdAt"] > timeout):
			return -1;
		else:
			return resp["data"];		

def set_route(pool,route,dictResponse):
	conn = redis.Redis(connection_pool=pool)
	resp = {"data":dictResponse,"createdAt":time.time()}
	pickle_dict = pickle.dumps(resp);
	conn.set(route,pickle_dict);

def reset(pool):
	conn = redis.Redis(connection_pool=pool)
	for i in conn.keys():
		conn.delete(i); 	