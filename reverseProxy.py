#!/usr/bin/env python3
__author__ = 'Ronak Kogta<rixor786@gmail.com>'
__description__ = \
''' Edge triggered Echo Server '''

import os;
import sys;
import socket;
import select;
import argparse;
import requests;
import lxml; 
import json;  

def parseconfig(configure_options):
	configure_options.add_argument('-p','--port', help='Enter port number', default=8001);
	configure_options.add_argument('--host', help='Enter host name', default='localhost');
	configure_options.add_argument('-c','--config', help='Enter config file', default='config.json');

def load_config(path):
	try:
		with open(path,'r') as f:
			configDict = json.loads( f.read() );
	except:
		print ("Error in processing config file");
		sys.exit(-1);		
	return configDict;	

def xml_to_json(response):
	toDict = xmltodict.parse(response);
	response = json.dumps(toDict,sort_keys = True, indent = 4, separators = (",",":") );
	del toDict; 
	return response;				

def connect_redis():
	return;

def connect_mongodb():
	return;

class server():
	def __init__(self,port,host,config_path):

		self.configDict = load_config(config_path);

		self.servSock = socket.socket( socket.AF_INET, socket.SOCK_STREAM );
		self.servSock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); 
		self.servSock.bind((host,port));
		self.servSock.listen(50);
		self.servSock.setblocking(0);
		
		# Via Disabling Nagle Theorem, echo server packets will not be buffered  
		self.servSock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1);

		# Intializing client dicts
		self.connections = {}; 
		self.responses = {}; 
				
		self.epoll = select.epoll()
		
		# Creating Epoll for future read events
		self.epoll.register(self.servSock.fileno(), select.EPOLLIN | select.EPOLLET);

		self.keep_alive_session=requests.Session();

		print ('NextBus Reverse Proxy[%s:%d] started' % (host,port));
		 

	def accept_connection(self):
		try:
			while True:
					clsock, (remote_host, remote_port) = self.servSock.accept();
					clsock.setblocking(0);
					self.epoll.register(clsock.fileno(), select.EPOLLIN | select.EPOLLET);
					self.connections[clsock.fileno()] = clsock;
					self.responses[clsock.fileno()] = "";
					print ('<connect> %d<-%d' % (self.servSock.fileno(),clsock.fileno()));
							
		except socket.error:
			pass;			

	def handle_read_events(self,fileno):
		try:
			while True:
				response = self.connections[fileno].recv(1024);
				self.epoll.modify(fileno, select.EPOLLOUT | select.EPOLLET); # Registering for write event 
				
				if (len(response) == 0):									 # Client quits 	
					self.responses[fileno] = "";
					break;

				self.responses[fileno] = response;
				self.request_handler(response); 
					 
		except socket.error:
			pass;		

	def handle_write_events(self,fileno):
		try:
			while(len(self.responses[fileno]) > 0):
				self.connections[fileno].send(self.responses[fileno]);
				self.responses[fileno] = "";
				self.epoll.modify(fileno, select.EPOLLIN | select.EPOLLET);		# Registering for read event
				break;
		except socket.error:
			pass;
		
		if len(self.responses[fileno]) == 0:									# Client quits
			self.epoll.modify(fileno, select.EPOLLET);
	   		self.connections[fileno].shutdown(socket.SHUT_RDWR)
	   		print ('<disconnect> %d<-%d' % (self.servSock.fileno(),fileno));

	def run(self):
		try:
		   while True:
		      events = self.epoll.poll(1);
		      for fileno, event in events:
		      	 
				if fileno == self.servSock.fileno():
					print "hi"									
					self.accept_connection(); 											  
									
				elif event & select.EPOLLIN:
					self.handle_read_events(fileno);
							
				elif event & select.EPOLLOUT:
					self.handle_write_events(fileno);

				elif event & select.EPOLLHUP:												# Client hang ups 
					self.epoll.unregister(fileno);
					self.connections[fileno].close();
					del self.connections[fileno];
					del self.responses[fileno];
		finally:
		   self.epoll.unregister(self.servSock.fileno());
		   self.epoll.close();
		   self.servSock.close();

	def request_handler(self,request):
		print (request);
		#req = self.keep_alive_session.get("http://webservices.nextbus.com/");
		#print (req.headers); 
		#print (req.text);	   

	 
	
	
	
		
	    
if __name__ == '__main__':
	configure_options = argparse.ArgumentParser(description = __description__);
	parseconfig(configure_options);
	args = configure_options.parse_args();
	
	thisserver = server(int(args.port),args.host,args.config);
	thisserver.run();
	
	