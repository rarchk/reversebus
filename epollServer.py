import logging
import select
import socket
import sys

import utilities


CONFIG_FILE = 'epollConfig.json'

HTTP_RESPONSE = {
	400: 'HTTP/1.0 400 OK\r\n',
	200: 'HTTP/1.0 200 OK\r\n'
}

''' Check if configuration file is properly set'''


def check_config(config_dict, logger):
	tcp_nagle = (type(config_dict['tcp_nagle']) == bool)
	tcp_cork = (type(config_dict['tcp_cork']) == bool)
	listen_connections = (type(config_dict['listen_connections']) == int)
	log = (type(config_dict['log']) == unicode)
	
	if not (tcp_nagle and tcp_cork and listen_connections and log):
		logger.error('Configuration file %s is not correctly configured' % CONFIG_FILE)
		sys.exit(-1)


class Server():
	def __init__(self, port, host, request_handler, parameters):

		# Registering configuration settings and request handler, logger
		self.config_dict = utilities.load_config(CONFIG_FILE)

		self.logger = logging.getLogger()
    		utilities.init_logger(self.logger, self.config_dict)

		check_config(self.config_dict, self.logger)
		
		self.request_handler = request_handler
		self.parameters = parameters

		self.servSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.servSock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.servSock.bind((host, port))
		self.servSock.listen(self.config_dict['listen_connections'])
		self.servSock.setblocking(0)
		
		if (self.config_dict['tcp_nagle']):
			self.servSock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

		# Intializing client dicts

                self.connections = {}
		self.responses = {}
				
		self.epoll = select.epoll()
		
		# Creating Epoll for future read events
		self.epoll.register(self.servSock.fileno(), select.EPOLLIN | select.EPOLLET)

		self.logger.info('NextBus Reverse Proxy[%s:%d] started' % (host, port))

	def accept_connection(self):
		try:
			while True:
					clsock, (rhost, rport) = self.servSock.accept()
					clsock.setblocking(0)
					self.epoll.register(clsock.fileno(), select.EPOLLIN | select.EPOLLET)
					self.connections[clsock.fileno()] = clsock
					self.responses[clsock.fileno()] = ""
					self.logger.info('[%s:%d] connected' % (rhost, rport))
							
		except socket.error:
			pass			

	def handle_read_events(self, fileno):
		try:
			while True:
				response = self.connections[fileno].recv(1024)
				self.epoll.modify(fileno, select.EPOLLOUT | select.EPOLLET)
				if (self.config_dict['tcp_cork']):
					self.connections[fileno].setsockopt(socket.IPPROTO_TCP, socket.TCP_CORK, 1)
				
				if (len(response) == 0):
					self.responses[fileno] = ""
					break

				(host, port) = self.connections[fileno].getpeername()
				response = self.request_handler([response, host, port], self.parameters)
				self.responses[fileno] = response
		except socket.error:
			pass		

	def handle_write_events(self, fileno):
		try:
			while(len(self.responses[fileno]) > 0):
				http_status, http_headers, response = self.responses[fileno]
				self.connections[fileno].send(HTTP_RESPONSE[http_status])
				self.connections[fileno].send(http_headers)
				self.connections[fileno].send(response)
				self.responses[fileno] = ""
				self.epoll.modify(fileno, select.EPOLLIN | select.EPOLLET)		# Registering for read event
				break
		except socket.error:
			pass
		
		if len(self.responses[fileno]) == 0:									# Client quits
			(host, port) = self.connections[fileno].getpeername()
			if (self.config_dict['tcp_cork']):
					self.connections[fileno].setsockopt(socket.IPPROTO_TCP, socket.TCP_CORK, 0)
			self.epoll.modify(fileno, select.EPOLLET)
	   		self.connections[fileno].shutdown(socket.SHUT_RDWR)
	   		self.logger.info('[%s:%d] disconnected' % (host,port))

	def disconnect(self, fileno):
		self.epoll.unregister(fileno)
		self.connections[fileno].close()
		del self.connections[fileno]
		del self.responses[fileno]

	def run(self):
		try:
		   while True:
		      events = self.epoll.poll(1)
		      for fileno, event in events:

				if fileno == self.servSock.fileno():
					self.accept_connection()

				elif event & select.EPOLLIN:
					self.handle_read_events(fileno)

				elif event & select.EPOLLOUT:
					self.handle_write_events(fileno)

				elif event & select.EPOLLHUP:
					self.disconnect(fileno)
		finally:
		   self.epoll.unregister(self.servSock.fileno())
		   self.epoll.close()
		   self.servSock.close()
