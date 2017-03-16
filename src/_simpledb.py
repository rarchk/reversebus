"""Methods for storing stats."""
import pymongo
from pymongo import MongoClient


def update(elapsed_time, route, config_dict):
	"""Update stats."""
	try:
		connection = MongoClient("localhost", 27017)
	except pymongo.errors.ConnectionFailure, e:
		print ("Could not connnect do MongoDB %s" % e)

	db = connection.stats
	slow_requests = db.slow_requests
	queries = db.queries

	if (elapsed_time > config_dict['slow_requests_threshold']):
		slow_requests.update({'endpoint': route}, {"$set": {"time": elapsed_time}}, upsert=True)

	endpoint_exists = queries.find({"endpoint": route})
	try:
		val = endpoint_exists.next()["value"]
		queries.update({'endpoint': route}, {"$set": {"value": val + 1}}, upsert=True)
	except StopIteration, e:
		queries.update({'endpoint': route}, {"$set": {"value": 1}}, upsert=True)


def show():
	"""Show stats."""
	connection = MongoClient("localhost", 27017)
	db = connection.stats
	slow_requests = db.slow_requests
	queries = db.queries
	json_response = '''{\n\t"slow_requests":{\n'''
	for d in slow_requests.find().sort([("endpoint", pymongo.DESCENDING)]):
		json_response += "\t\t\"" + d['endpoint'] + "\": " + str(d['time']) + ",\n"

	json_response += "\t},\n\t\"queries\":{\n"

	for d in queries.find().sort([("endpoint", pymongo.DESCENDING)]):
		json_response += "\t\t\"" + d['endpoint'] + "\": " + str(d['value']) + ",\n"
	
	json_response += "\t}\n}"

	return json_response
