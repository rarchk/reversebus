import argparse
import logging
import sys
import time

import caching

import epollServer as epoll

import requests

import stats

import utilities

__author__ = 'Ronak Kogta<rixor786@gmail.com>'
__description__ = ''' Edge triggered Reverse proxy broker '''
__help_response__ = '''Reverse proxy for NextBus API.\r\n 
We do not have appropriate response for above request. 
Please refer https://github.com/rarchk/reversebus#examples'''

logger = logging.getLogger()
CONFIG_FILE = ''

''' Handles cmdline argumets'''


def parseConfig(configure_options):
	configure_options.add_argument('-p', '--port', help='Enter port number', default=8001)
	configure_options.add_argument('--host', help='Enter host name', default='localhost')
	configure_options.add_argument('-c', '--config', help='Enter config file', default='config.json')

''' Check if configuration file is properly set'''


def check_config(config_dict, logger):
	target_url = (type(config_dict['target_url']) == unicode)
	mongodb_address = (type(config_dict['mongodb_address']) == unicode)
	redis_address = (type(config_dict['redis_address']) == unicode)
	log = (type(config_dict['log']) == unicode)
	redis_port = (type(config_dict['redis_port']) == int)
	mongodb_port = (type(config_dict['mongodb_port']) == int)
	redis_timeout = (type(config_dict['redis_timeout']) == int)
	slow_requests_threshold = (type(config_dict['slow_requests_threshold']) == float)
	
	if not (target_url and mongodb_address and redis_address and log and\
	 redis_port and mongodb_port and redis_timeout and slow_requests_threshold):
		logger.error('Configuration file %s is not correctly configured' % CONFIG_FILE)
		sys.exit(-1)


def request_handler(epoll_context, parameters):
	startTime = time.time()
	request, host, port = epoll_context
	config_dict, pool = parameters
	
	try:
		route, query_url = getRoute(request, config_dict)
		
		
		if (query_url == ""):
			json_response = __help_response__

		elif (query_url == "stats"):
			json_response = stats.show()
		else:
			response = caching.get_route(pool, route, config_dict['redis_timeout'])
			if(response == -1):
				xml_response = requests.get(query_url)
				json_response, dict_response = utilities.to_json(xml_response.text, "xml")
				caching.set_route(pool, route, dict_response)
				
			else:
				json_response, _ = utilities.to_json(response,"dict")

		elapsed_time = time.time() - startTime
		if (query_url != "stats" or query_url != ""):
			stats.update(elapsed_time, route, config_dict)
		
		logger.info("%s took %fs" % (route, elapsed_time))
		return ['HTTP/1.0 200 OK\r\n', "Content-Type: application/json\r\n\r\n", str(json_response)]

	except Exception as e:
		logger.error("Error in handling request:%s" % (e))
		return ['HTTP/1.0 400 OK\r\n', "Content-Type: application/json\r\n\r\n", __help_response__]
	
def getRoute(request,config_dict):
	route = ""
	query_url = config_dict['target_url'] + "/service/publicXMLFeed?command="
	
	for header in request.split("\r\n"):
		if ("GET" in header):
			route = header.split(" ")[1]
			break
	try:		
		routers = route.split("/")
	except:
		logger.error("Not a get request from client")	

	if (route == "/"):
		return [route, ""]

	shortTitles= ""
	query_points= []
	if ('useShortTitles' == unicode(routers[-1])):
		shortTitles += "&useShortTitles=True"
		del routers[-1]

	if ('stats' == unicode(routers[3])):
		query_url = "stats"
		return [route, query_url]

	elif ('agencyList' == unicode(routers[3])):
		query_url += "agencyList"
		return [route, query_url]

	elif ('routeList' == unicode(routers[3])):
		query_points = ["routeList&a="]
		
	elif ('routeConfig' == unicode(routers[3])):
		query_points = ["routeConfig&a=", "&r="]
		
	elif ('predictByStopId' == unicode(routers[3])):
		query_points = ["predictions&a=", "&stopId=", "&routeTag="]
		
	elif ('predictByStop' == unicode(routers[3])):
		query_points = ["predictions&a=", "&r=", "&s="]
		
	elif ('schedule' == unicode(routers[3])):
		query_points = ["schedule&a=", "&r="]
		
	elif ('vehicleLocations' == unicode(routers[3])):
		query_points = ["vehicleLocations&a=", "&r=", "&t="]
	
	elif ('messages' == unicode(routers[3])):
		query_points = ["messages&a=", "&r="]
	
	elif ('predictionsForMultiStops' == unicode(routers[3])):
		query_points = ["predictionsForMultiStops&a=", "&stops="]
			
	else:
		logger.error("API request '%s' not recognized" % str(route))
		raise Exception

	query_url += generateUrl(4, query_points, routers) + shortTitles

	return [route, query_url]

def generateUrl(index, query_points, routers):
	query_url = ""
	last_query_point = ""
	for i in range(index, len(routers), 1):
		try:
			last_query_point = str(query_points[i - index])
		except:
			pass
		query_url += last_query_point + str(routers[i])
	return query_url

if __name__ == '__main__':
	configure_options = argparse.ArgumentParser(description=__description__)
	parseConfig(configure_options)
	args = configure_options.parse_args()

	CONFIG_FILE = args.config
	config_dict = utilities.load_config(CONFIG_FILE)
	utilities.init_logger(logger, config_dict)
	check_config(config_dict, logger)
	pool = caching.init(config_dict)

	thisserver = epoll.Server(int(args.port), args.host, request_handler, [config_dict,pool])
	thisserver.run()
