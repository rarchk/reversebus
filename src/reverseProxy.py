"""Reverse proxy for Next Bus server."""
import argparse
import logging
import re
import sys
import time
import gzip
import StringIO

import _cache

import _epollserver as epoll

import requests

import _simpledb

import _utilities

__author__ = 'Ronak Kogta<rixor786@gmail.com>'
__description__ = ''' Edge triggered Reverse proxy broker '''
_default_response_ = '''Reverse proxy for NextBus API.\r\n
We do not have appropriate response for above request.
Please refer https://github.com/rarchk/reversebus#examples'''

logger = logging.getLogger()

# API endpoints with their query points
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


def parse_config(configure_options):
        """Parse configuration from commmand line."""
	configure_options.add_argument('-p', '--port', help='Enter port number',
     default=8001)
	configure_options.add_argument('--host', help='Enter host name',
     default='localhost')
	configure_options.add_argument('-c', '--config', help='Enter config file',
     default='config.json')


def check_config(config_dict, logger, config_file):
        """Check if config file is correct."""
	bool1 = (type(config_dict['target_url']) == unicode)
	bool2 = (type(config_dict['mongodb_address']) == unicode)
	bool3 = (type(config_dict['redis_address']) == unicode)
	bool4 = (type(config_dict['log']) == unicode)
	bool5 = (type(config_dict['redis_port']) == int)
	bool6 = (type(config_dict['mongodb_port']) == int)
	bool7 = (type(config_dict['redis_timeout']) == int)
	bool8 = (type(config_dict['slow_requests_threshold']) == float)
	
	if not (bool1 and bool2 and bool3 and bool4 and bool5 and bool6 and
     bool7 and bool8):
		logger.error('Configuration file %s is not correctly configured'
         % config_file)
		sys.exit(-1)


def request_handler(epoll_context, parameters):
        """Application level request handler."""
	startTime = time.time()
	request, host, port = epoll_context
	config_dict, pool = parameters
	
	try:
		route, query_url, gzip_flag = get_route(request, config_dict)

		if (query_url == ""):
			json_response = _default_response_

		elif (query_url == "stats"):
			json_response = _simpledb.show()
		else:
			response = _cache.get_route(pool, route, config_dict['redis_timeout'])
			if(response == -1):
				xml_response = requests.get(query_url)
				json_response, dict_response = _utilities.to_json(xml_response.text, "xml")
				_cache.set_route(pool, route, dict_response)

				
			else:
				json_response, _ = _utilities.to_json(response, "dict")

                json_response, headers = to_gzip_response(json_response, gzip_flag)

		elapsed_time = time.time() - startTime
		if (query_url != "stats" or query_url != ""):
			_simpledb.update(elapsed_time, route, config_dict)
		
		logger.info("%s took %fs" % (route, elapsed_time))

		return [200, headers, str(json_response)]

	except Exception as e:
                ex_resp, headers = to_gzip_response(_default_response_,gzip_flag)
		logger.error("Error in handling request:%s" % (e))
		return [400, headers, ex_resp]
	

def get_route(request, config_dict):
        """Get routes for api endpoints."""

        try:
	         route = re.search("GET (.*) HTTP", request).group(1)
        except:
                 logger.error("Not a get request from client")
                 raise Exception
                 return
        try:
             encoding = re.search("Accept-Encoding: (.*)", request).group(1)
             gzip_flag = ("gzip" in encoding)
        except:
             gzip_flag = False

	query_url = config_dict['target_url'] + "/service/publicXMLFeed?command="
	routers = route.split("/")
			
	if (route == "/"):
		return [route, "", gzip_flag]

	short = ""
	if ('useShortTitles' == str(routers[-1])):
		short = API_ENDPOINTS['useShortTitles']
		del routers[-1]
        try:
            query_url = next_xml_url(query_url, API_ENDPOINTS[str(routers[3])],
             routers) + short
            print query_url
            return [route, query_url, gzip_flag]
        except Exception as e:
            logger.error("Request '%s returned with %s " % (str(route), e))


def next_xml_url(query_url, query_points, routers):
    """Generate xml url based on next api endpoints."""
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

def to_gzip_response(response,gzip_flag):
    """ Return gzip compliant response and headers."""
    headers = "Content-Type: application/json\r\n"
    if (gzip_flag):
        out = StringIO.StringIO()
        with gzip.GzipFile(fileobj=out, mode="w") as f:
            f.write(response)
        headers += "Vary: Accept-Encoding\r\n"
        headers += "Content-Encoding: gzip\r\n\r\n"
        response = out.getvalue()
        del out
    else:
        headers += "\r\n"    
    return [response,headers]        


if __name__ == '__main__':
	configure_options = argparse.ArgumentParser(description=__description__)
	parse_config(configure_options)
	args = configure_options.parse_args()

	config_dict = _utilities.load_config(args.config)
	_utilities.init_logger(logger, config_dict)
	check_config(config_dict, logger, args.config)
	pool = _cache.init(config_dict)

	thisserver = epoll.Server(int(args.port), args.host, request_handler,
     [config_dict, pool])
	thisserver.run()
