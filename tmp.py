#!/usr/bin/env python
__author__ = 'Ronak Kogta<rixor786@gmail.com>'
__description__ = \
''' Edge triggered Reverse proxy broker '''

import os;
import sys;
import argparse;
import requests;
import xmltodict; 
import json;
from epollServer import *;   

def parseconfig(configure_options):
	configure_options.add_argument('-p','--port', help='Enter port number', default=8001);
	configure_options.add_argument('--host', help='Enter host name', default='localhost');
	configure_options.add_argument('-c','--config', help='Enter config file', default='config.json');

def load_config(path):
	try:
		with open(path,'r') as f:
			configDict = json.loads( f.read() );
	except:
		print ("Bad configuration file name");
		sys.exit(-1);		
	return configDict;	

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

def my_request_handler(request,configDict):
	query_url = get_http_route(request,configDict);
	xml_response = requests.get(query_url);
	json_response =  xml_to_json(xml_response.text);
	
	http_request = "content-type: application/json\r\n\r\n" + json_response; 
	return http_request;
	
def get_http_route(request,configDict):
	route = ""
	base_url = configDict['target_url']
	query_url = "/service/publicXMLFeed?command="
	
	for header in request.split("\r\n"):
		if ("GET" in header):
			route = header.split(" ")[1];
			break;
	routers = route.split("/");

	if ('agencyList' in str(routers[2])):
		print 1
		query_url = base_url + query_url + "agencyList";

	elif ('routeList' in str(routers[2])):
		query_url = base_url + query_url + "routeList&a=" + str(routers[3]);

	elif ('stats' in str(routers[2])):
		query_url = "";

	elif ('routeConfig' in str(routers[2])):
		query_url = base_url + query_url + "routeConfig&a=" + str(routers[3]) + "&r=" + str(routers[4]);

	elif ('predictByStopId' in str(routers[2])):
		query_url = base_url + query_url + "routeList&a=";
	
	elif ('predictByStop' in str(routers[2])):
		query_url = base_url + query_url + "routeList&a=";
	
	elif ('predictionsForMultiStops' in str(routers[2])):
		query_url = base_url + query_url + "routeList&a=";
	
	elif ('schedule' in str(routers[2])):
		query_url = base_url + query_url + "routeList&a=";
	
	elif ('vehicleLocations' in str(routers[2])):
		query_url = base_url + query_url + "routeList&a=";

	else:
		query_url = "";

	return query_url;				
			   

if __name__ == '__main__':
	configure_options = argparse.ArgumentParser(description = __description__);
	parseconfig(configure_options);
	args = configure_options.parse_args();

	config_dict = load_config(args.config);
	
	thisserver = epollServer(int(args.port),args.host,config_dict,my_request_handler);
	thisserver.run();
	
	