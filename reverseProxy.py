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
import epollServer as epoll;
import time;
import stats;
import redis;
import caching; 
 
    

def parseconfig(configure_options):
	configure_options.add_argument('-p','--port', help='Enter port number', default=8001);
	configure_options.add_argument('--host', help='Enter host name', default='localhost');
	configure_options.add_argument('-c','--config', help='Enter config file', default='config.json');


def request_handler(epollContext,parameters):
	startTime = time.time();
	request,host,port = epollContext;
	configDict,pool = parameters;
	
	try:
		route,queryUrl = get_http_route(request,configDict);
		
		
		if (queryUrl == ""):
			jsonResponse = __help_response__;

		elif (queryUrl == "stats"):
			jsonResponse = stats.show();
		else:
			response = caching.get_route(pool,route,configDict['redis_timeout'])	
			if(response == -1):
				xmlResponse = requests.get(queryUrl);
				jsonResponse,dictResponse =  caching.toJson(xmlResponse.text,"xml");
				caching.set_route(pool,route,dictResponse);
				
			else:
				jsonResponse, _ = caching.toJson(response,"dict")	

		elapsedTime = time.time() - startTime
		if (queryUrl != "stats"):
			stats.update(elapsedTime,route,configDict);
		
		http_response =  str(elapsedTime) + "\n" + queryUrl + "\n" + str(jsonResponse);
		return http_response;

	except Exception as e:
		return ("Bad request: %s\n%s" % (e,__help_response__));
	
def get_http_route(request,configDict):
	route = ""
	queryUrl = configDict['target_url'] + "/service/publicXMLFeed?command="
	
	for header in request.split("\r\n"):
		if ("GET" in header):
			route = header.split(" ")[1];
			break;
	routers = route.split("/");

	if (route == "/"):
		return [route,""];

	shortTitles=""
	if ('useShortTitles' == str(routers[-1])):
		shortTitles += "&useShortTitles=True"
		del routers[-1];

	if ('agencyList' == str(routers[3])):
		query_points = ["agencyList"];
		queryUrl += str(query_points[0]);

	elif ('routeList' == str(routers[3])):
		query_points = ["routeList&a="];
		for i in range(4,len(routers),1):
			queryUrl += str(query_points[i-4]) + str(routers[i]);
		

	elif ('stats' == str(routers[3])):
		queryUrl = "stats";

	elif ('routeConfig' == str(routers[3])):
		query_points = ["routeConfig&a=","&r="];
		for i in range(4,len(routers),1):
			queryUrl += str(query_points[i-4]) + str(routers[i]);
		queryUrl += shortTitles;
		

	elif ('predictByStopId' == str(routers[3])):
		query_points = ["predictions&a=","&stopId=","&routeTag="];
		for i in range(4,len(routers),1):
			queryUrl += str(query_points[i-4]) + str(routers[i]);
		queryUrl += shortTitles;	
		
	elif ('predictByStop' == str(routers[3])):
		query_points = ["predictions&a=","&r=","&s="];
		for i in range(4,len(routers),1):
			queryUrl += str(query_points[i-4]) + str(routers[i]);
		queryUrl += shortTitles;
		
	
	elif ('predictionsForMultiStops' == str(routers[3])):
		query_points = ["predictionsForMultiStops&a=","&stops="];
		queryUrl += str(query_points[0]) + str(routers[4]);
		for i in range(5,len(routers),1):
			queryUrl += str(query_points[1]) + str(routers[i]);
		queryUrl += shortTitles;
	
	elif ('schedule' == str(routers[3])):
		query_points = ["schedule&a=","&r="];
		for i in range(4,len(routers),1):
			queryUrl += str(query_points[i-4]) + str(routers[i]);
		
	
	elif ('vehicleLocations' == str(routers[3])):
		query_points = ["vehicleLocations&a=","&r=","&t="];
		for i in range(4,len(routers),1):
			queryUrl += str(query_points[i-4]) + str(routers[i]);

	elif ('messages' == str(routers[3])):
		query_points = ["messages&a=","&r="];
		queryUrl += str(query_points[0]) + str(routers[4]);
		for i in range(5,len(routers),1):
			queryUrl += str(query_points[1]) + str(routers[i]);
				
	else:
		raise Exception;

	return [route,queryUrl];				
			   

if __name__ == '__main__':
	configure_options = argparse.ArgumentParser(description = __description__);
	parseconfig(configure_options);
	args = configure_options.parse_args();

	configDict = epoll.load_config(args.config);
	pool = redis.ConnectionPool(host='localhost', port=configDict['redis_port'], db=0)
	
	thisserver = epoll.server(int(args.port),args.host,request_handler,[configDict,pool]);
	thisserver.run();
	
	