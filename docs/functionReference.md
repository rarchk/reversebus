Basic Function Reference for ReverseProxy 
===

## Epollserver

```python
class server():
	def __init__ (request_handler,parameters):
    	...
    def run():
    	...
    def accept_connections():
    	...
    def handle_write_events():
    	...
    def handle_read_events():
    	...
```	

Above class exposes a `request_handler` function and user defined `parameters`, which can be implemented at application level. It also serves an `epollContext` to feed the state of current connection 

```python
def request_handler(epollContext,parameters):
	raw_request,host,port = epollContext;
	configDict,pool = parameters;
```

**Things to be done**

- Cannot handle session based queries well, designed for short term connections from client side.


