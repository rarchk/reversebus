#!/usr/bin/env python
__author__ = 'Ronak Kogta<rixor786@gmail.com>'
__description__ = \
''' Edge triggered Reverse proxy broker '''
__help_response__ = \
'''Reverse proxy for NextBus API.\r\n 
We do not have appropriate response for above request. 
Please refer https://github.com/rarchk/reversebus#examples'''

import os;
import sys;
import argparse;
import requests;
import time;
import logging;

import stats;
import caching;
import utilities;  
import epollServer as epoll;

logger = logging.getLogger()
CONFIG_FILE = ''

''' Handles cmdline argumets'''
def parseConfig(configure_options):
	configure_options.add_argument('-p','--port', help='Enter port number', default=8001);
	configure_options.add_argument('--host', help='Enter host name', default='localhost');
	configure_options.add_argument('-c','--config', help='Enter config file', default='config.json');

''' Check if configuration file is properly set'''
def checkConfig(configDict,logger):
	target_url = (type(configDict['target_url']) == str);
	mongodb_address = (type(configDict['mongodb_address']) == str);
	redis_address = (type(configDict['redis_address']) == str);
	log = (type(configDict['log']) == str);
	redis_port = (type(configDict['redis_port']) == int);
	mongodb_port = (type(configDict['mongodb_port']) == int);
	redis_timeout = (type(configDict['redis_timeout']) == int);
	slow_requests_threshold = (type(configDict['slow_requests_threshold']) == float);
	
	if not (target_url and mongodb_address and redis_address and log and\
	 redis_port and mongodb_port and redis_timeout and slow_requests_threshold):
		logger.error('Configuration file %s is not correctly configured' % CONFIG_FILE);
		sys.exit(-1);


def requestHandler(epollContext,parameters):
	startTime = time.time();
	request,host,port = epollContext;
	configDict,pool = parameters;
	
	try:
		route,queryUrl = getRoute(request,configDict);
		
		
		if (queryUrl == ""):
			jsonResponse = __help_response__;

		elif (queryUrl == "stats"):
			jsonResponse = stats.show();
		else:
			response = caching.get_route(pool,route,configDict['redis_timeout'])	
			if(response == -1):
				xmlResponse = requests.get(queryUrl);
				jsonResponse,dictResponse =  utilities.toJson(xmlResponse.text,"xml");
				caching.set_route(pool,route,dictResponse);
				
			else:
				jsonResponse, _ = utilities.toJson(response,"dict")	

		elapsedTime = time.time() - startTime
		if (queryUrl != "stats" or queryUrl != ""):
			stats.update(elapsedTime,route,configDict);
		
		logger.info("%s took %fs" %(route,elapsedTime));
		return ['HTTP/1.0 200 OK\r\n',"Content-Type: application/json\r\n\r\n",str(jsonResponse)];

	except Exception as e:
		logger.error("Error in handling request:%s" % (e));
		return ['HTTP/1.0 400 OK\r\n',"Content-Type: application/json\r\n\r\n",__help_response__];
	
def getRoute(request,configDict):
	route = ""
	queryUrl = configDict['target_url'] + "/service/publicXMLFeed?command="
	
	for header in request.split("\r\n"):
		if ("GET" in header):
			route = header.split(" ")[1];
			break;
	try:		
		routers = route.split("/");
	except:
		logger.error("Not a get request from client");	

	if (route == "/"):
		return [route,""];

	shortTitles=""
	query_points=[];
	if ('useShortTitles' == str(routers[-1])):
		shortTitles += "&useShortTitles=True"
		del routers[-1];

	if ('stats' == str(routers[3])):
		queryUrl = "stats";
		return [route,queryUrl];

	elif ('agencyList' == str(routers[3])):
		queryUrl += "agencyList";
		return [route,queryUrl];

	elif ('routeList' == str(routers[3])):
		query_points = ["routeList&a="];
		
	elif ('routeConfig' == str(routers[3])):
		query_points = ["routeConfig&a=","&r="];
		
	elif ('predictByStopId' == str(routers[3])):
		query_points = ["predictions&a=","&stopId=","&routeTag="];
		
	elif ('predictByStop' == str(routers[3])):
		query_points = ["predictions&a=","&r=","&s="];
		
	elif ('schedule' == str(routers[3])):
		query_points = ["schedule&a=","&r="];
		
	elif ('vehicleLocations' == str(routers[3])):
		query_points = ["vehicleLocations&a=","&r=","&t="];
	
	elif ('messages' == str(routers[3])):
		query_points = ["messages&a=","&r="];
	
	elif ('predictionsForMultiStops' == str(routers[3])):
		query_points = ["predictionsForMultiStops&a=","&stops="];
			
	else:
		logger.error("API request '%s' not recognized" % str(route))
		raise Exception;

	queryUrl += generateUrl(4,query_points,routers) + shortTitles;	

	return [route,queryUrl];				

def generateUrl(index,query_points,routers):
	queryUrl = "";
	last_query_point = ""
	for i in range(index,len(routers),1):
		try:
			last_query_point = str(query_points[i-index]);
		except:
			pass;	
		queryUrl += last_query_point + str(routers[i]);
	return queryUrl;		
			   
if __name__ == '__main__':
	configure_options = argparse.ArgumentParser(description = __description__);
	parseConfig(configure_options);
	args = configure_options.parse_args();

	CONFIG_FILE = args.config;
	configDict = utilities.loadConfig(CONFIG_FILE);
	utilities.initLogger(logger,configDict);
	checkConfig(configDict,logger)
	pool = caching.init(configDict);

	thisserver = epoll.server(int(args.port),args.host,requestHandler,[configDict,pool]);
	thisserver.run();
	 	
	
	