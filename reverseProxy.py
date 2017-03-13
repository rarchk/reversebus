import argparse
import logging
import re
import sys
import time

import caching

import epollServer as epoll

import requests

import stats

import utilities

__author__ = 'Ronak Kogta<rixor786@gmail.com>'
__description__ = ''' Edge triggered Reverse proxy broker '''
_default_response_ = '''Reverse proxy for NextBus API.\r\n
We do not have appropriate response for above request.
Please refer https://github.com/rarchk/reversebus#examples'''

logger = logging.getLogger()


API_ENDPOINTS = {
    "useShortTitles": "&useShortTitles=True",
    "agencyList": ["agencyList"],
    "routeList": ["routeList&a="],
    "routeConfig": ["routeConfig&a=", "&r="],
    "messages": ["messages&a=", "&r="],
    "predictByStop": ["predictions&a=", "&r=", "&s="],
    "predictByStopId": ["predictions&a=", "&stopId=", "&routeTag="],
    "predictionsForMultiStops": ["predictionsForMultiStops&a=", "&stops="],
    "vehicleLocations": ["vehicleLocations&a=", "&r=", "&t="],
    "schedule": ["schedule&a=", "&r="],
    "stats": ["stats"]
}

''' Handles cmdline argumets'''


def parse_config(configure_options):
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
		route, query_url = get_route(request, config_dict)
		
		
		if (query_url == ""):
			json_response = _default_response_

		elif (query_url == "stats"):
			json_response = stats.show()
		else:
			response = caching.get_route(pool, route, config_dict['redis_timeout'])
			if(response == -1):
				xml_response = requests.get(query_url)
				json_response, dict_response = utilities.to_json(xml_response.text, "xml")
				caching.set_route(pool, route, dict_response)
				
			else:
				json_response, _ = utilities.to_json(response, "dict")

		elapsed_time = time.time() - startTime
		if (query_url != "stats" or query_url != ""):
			stats.update(elapsed_time, route, config_dict)
		
		logger.info("%s took %fs" % (route, elapsed_time))
		return [200, "Content-Type: application/json\r\n\r\n", str(json_response)]

	except Exception as e:
		logger.error("Error in handling request:%s" % (e))
		return [400,"Content-Type: application/json\r\n\r\n", _default_response_]
	

def get_route(request, config_dict):
        try:
	         route = re.search("GET (.*) HTTP", request).group(1)
        except:
                 logger.error("Not a get request from client")
                 raise Exception
                 return

	query_url = config_dict['target_url'] + "/service/publicXMLFeed?command="
	routers = route.split("/")
			
	if (route == "/"):
		return [route, ""]

	short = ""
	if ('useShortTitles' == str(routers[-1])):
		short = API_ENDPOINTS['useShortTitles']
		del routers[-1]
        try:
            query_url = next_xml_url(query_url, API_ENDPOINTS[str(routers[3])], routers) + short
            print query_url
            return [route, query_url]
        except Exception as e:
            logger.error("Request '%s returned with %s " % (str(route),e))


def next_xml_url(query_url, query_points, routers):
    index = 4
    last_query_point = ""
    query = str(query_points[0])
    if (query == "stats"):
        return "stats"
    elif (query == "agencyList"):
        return query_url + "agencyList"

    for i in range(index, len(routers), 1):
	try:
		last_query_point = str(query_points[i - index])
	except:
		pass
	query_url += last_query_point + str(routers[i])
	
    return query_url

if __name__ == '__main__':
	configure_options = argparse.ArgumentParser(description=__description__)
	parse_config(configure_options)
	args = configure_options.parse_args()

	config_dict = utilities.load_config(args.config)
	utilities.init_logger(logger, config_dict)
	check_config(config_dict, logger)
	pool = caching.init(config_dict)

	thisserver = epoll.Server(int(args.port), args.host, request_handler, [config_dict,pool])
	thisserver.run()
