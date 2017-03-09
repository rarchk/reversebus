from pymongo import MongoClient;
import pymongo;

  
def update(elapsedTime,route,configDict):
	try:
		connection = MongoClient("localhost",27017);
	except pymongo.errors.ConnectionFailure, e:
		print ("Could not connnect do MongoDB %s" % e);
			
	db = connection.stats;
	slow_requests = db.slow_requests;
	queries = db.queries;

	if (elapsedTime > configDict['slow_requests_threshold']):
		slow_request = {'endpoint':route,'time':elapsedTime};
		slow_requests.update({'endpoint':route},{"$set":{"time":elapsedTime}}, upsert=True);
		
	endpointExists = queries.find({"endpoint":route}); 
	try:
		val = endpointExists.next()["value"];
		queries.update({'endpoint':route},{"$set":{"value":val+1}}, upsert=True);
	except StopIteration, e:
		queries.update({'endpoint':route},{"$set":{"value":1}}, upsert=True);

def show():
	connection = MongoClient("localhost",27017);
	db = connection.stats;
	slow_requests = db.slow_requests;
	queries = db.queries;
	json_response='''{\n\t"slow_requests":{\n'''
	for d in slow_requests.find().sort([("endpoint", pymongo.DESCENDING)]):
		json_response += "\t\t\"" + d['endpoint'] + "\": " + str(d['time']) + ",\n"

	json_response += "\t},\n\t\"queries\":{\n"	

	for d in queries.find().sort([("endpoint", pymongo.DESCENDING)]):
		json_response += "\t\t\"" + d['endpoint'] + "\": " + str(d['value']) + ",\n"
	
	json_response += "\t}\n}"	

	return json_response 		 
