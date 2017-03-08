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
import xmltodict; 
import json;
import epollServer as epoll;
import time;    

def parseconfig(configure_options):
	configure_options.add_argument('-p','--port', help='Enter port number', default=8001);
	configure_options.add_argument('--host', help='Enter host name', default='localhost');
	configure_options.add_argument('-c','--config', help='Enter config file', default='config.json');

def xml_to_json(response):
	toDict = xmltodict.parse(response);
	response = json.dumps(toDict,sort_keys = True, indent = 4, separators = (",",":") );
	del toDict; 
	return response;				

def connect_redis():
	return;
	pass

def connect_mongodb():
	return;
	pass

def my_request_handler(epollContext,parameters):
	startTime = time.time();
	request = str(epollContext[0]);
	host = str(epollContext[1]);
	port = int(epollContext[2]);
	configDict = dict(parameters[0]);
	
	try:
		query_url = get_http_route(request,configDict);
		if (query_url == ""):
			json_response = __help_response__;

		elif (query_url == "stats"):
			json_response = "need stats code now";
		else:		
			xml_response = requests.get(query_url);
			json_response =  xml_to_json(xml_response.text);
	
		return str(time.time() - startTime) + "\n" + query_url + "\n" + json_response;
	except Exception as e:
		return ("Bad request: %s\n%s" % (request,__help_response__));
		 
	
def get_http_route(request,configDict):
	route = ""
	query_url = configDict['target_url'] + "/service/publicXMLFeed?command="
	
	for header in request.split("\r\n"):
		if ("GET" in header):
			route = header.split(" ")[1];
			break;
	routers = route.split("/");

	if (route == "/"):
		return "";

	shortTitles=""
	if ('useShortTitles' in str(routers[-1])):
		shortTitles += "&useShortTitles=True"
		del routers[-1];

	if ('agencyList' in str(routers[3])):
		query_points = ["agencyList"];
		query_url += str(query_points[0]);

	elif ('routeList' in str(routers[3])):
		query_points = ["routeList&a="];
		for i in range(4,len(routers),1):
			query_url += str(query_points[i-4]) + str(routers[i]);
		

	elif ('stats' in str(routers[3])):
		query_url = "stats";

	elif ('routeConfig' in str(routers[3])):
		query_points = ["routeConfig&a=","&r="];
		for i in range(4,len(routers),1):
			query_url += str(query_points[i-4]) + str(routers[i]);
		query_url += shortTitles;
		

	elif ('predictByStopId' in str(routers[3])):
		query_points = ["predictions&a=","&stopId=","&routeTag="];
		for i in range(4,len(routers),1):
			query_url += str(query_points[i-4]) + str(routers[i]);
		query_url += shortTitles;	
		
	elif ('predictByStop' in str(routers[3])):
		query_points = ["predictions&a=","&r=","&s="];
		for i in range(4,len(routers),1):
			query_url += str(query_points[i-4]) + str(routers[i]);
		query_url += shortTitles;
		
	
	elif ('predictionsForMultiStops' in str(routers[3])):
		query_points = ["predictionsForMultiStops&a=","&stops="];
		query_url += str(query_points[0]) + str(routers[4]);
		for i in range(5,len(routers),1):
			query_url += str(query_points[1]) + str(routers[i]);
		query_url += shortTitles;
	
	elif ('schedule' in str(routers[3])):
		query_points = ["schedule&a=","&r="];
		for i in range(4,len(routers),1):
			query_url += str(query_points[i-4]) + str(routers[i]);
		
	
	elif ('vehicleLocations' in str(routers[3])):
		query_points = ["vehicleLocations&a=","&r=","&t="];
		for i in range(4,len(routers),1):
			query_url += str(query_points[i-4]) + str(routers[i]);

	elif ('messages' in str(routers[3])):
		query_points = ["messages&a=","&r="];
		query_url += str(query_points[0]) + str(routers[4]);
		for i in range(5,len(routers),1):
			query_url += str(query_points[1]) + str(routers[i]);
				
	else:
		raise Exception;

	return query_url;				
			   

if __name__ == '__main__':
	configure_options = argparse.ArgumentParser(description = __description__);
	parseconfig(configure_options);
	args = configure_options.parse_args();

	configDict = epoll.load_config(args.config);
	
	thisserver = epoll.server(int(args.port),args.host,my_request_handler,[configDict]);
	thisserver.run();
	
	