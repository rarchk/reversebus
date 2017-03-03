NextBus Reverse Proxy
===

A simple reverse proxy for San Francisco's public transportation powered by NextBus's XML feed.   

## Installation 

It depends on 

- python2.7
	- pymongo=3.4
	- requests
	- xmltodict
- MongoDB 
- Redis Cache
- Docker

## Usage

## Design Specification
<img src="reverseproxy.png" width="100%" height="auto"/>

### Configuration
You can configure following parameters in `config.json`
- mongoDb_address  and mongoDb_port 
- redis_adress and redis_port 
- slow_requests_rate 


## API Endpoints
The application address is, by default, `127.0.0.1:8080/`. A brief description of all the end points are given below. `api/stats` endpoint is particular to the state of reverse proxy

|*api/stats*| Exposes Statistics |
|:---:|:---|
|*slow_requests*| Lists the endpoints which had response time higher a certain threshold along with the time taken.|
|*queries*|List all the endpoints queried by the user along with the number of requests for each.|

|End points| Description | 
|:---|:---|
|*api/agencyList*| Lists all agencies.|
|*api/routeList/{agency}*| Lists all the routes for the agency tag supplied.
|*api/routeConfig/{agency}/{route}*| Lists all the stops for the route tag supplied.
|*api/predictByStopId/{agency}/{stopId}*| Lists arrival/departure predictions for a stop.|
|*api/predictByStop/{agency}/{route}/{stop}*| Same as predictByStopId but using the *{stop}* tag instead *{route}* tag is required because *{stop}* tag is associated with a route.  
|*api/predictionsForMultiStops/{agency}/{stops}*| Lists arrival/departure predictions for multi-stops. The format of the *{stops}* tag is *route or stop* . Append more *{/stops}* for more stops.|
|*api/schedule/{agency}/{route}*| Obtain the schedule information for a given *{agency}* and *{route}* tags
|*api/messages/{agency}/{route}*| List the active messages for the selected route. Append *{/route}*for more routes.
|*api/vehicleLocations/{agency}/{route}/{time}*| Lists vehicle locations for the selected *{route}*. *{time}* tag is in msec since the 1970 epoch time. If you specify a time of 0, then data for the last 15 minutes is provided.
  
- Get *{agency}* tags using `agencyList`
-  Get *{route}* tags using `routeList`, 
-  Get*{stop}* and *{stopId}* tags using `routeConfig`.
- A */{route}* tag  can be appended if predictions for only one route are desired.
-  Append `&useShortTitles=true` to have the XML feed return short titles intended for display devices with small screens.


### Examples
   - `api/routeList/sf-muni`
   - `api/routeConfig/sf-muni/E`
   - `api/predictByStopId/sf-muni/15184`
   - `api/predictByStop/sf-muni/E/5184`
   - `api/predictionsForMultiStops/sf-muni/N|6997`		
   - `api/schedule/sf-muni/E`
   - `api/vehicleLocations/sf-muni/E/0`
   
## Data Schema
We have used MongoDB for our database, as it is highly available and is a good fit for storing meta data. We write statistics to MongoDB as we want our reverse proxy brokers to have a unified view of data `(slow_request,queries)`

## Caching
To be done by Redis 
## References 
- [Next Bus XML Feed Documentation](http://www.nextbus.com/xmlFeedDocs/NextBusXMLFeed.pdf)
- [Caching is hard, draw me a picture](http://bizcoder.com/caching-is-hard-draw-me-a-picture)
- [Problems with caching](https://msol.io/blog/tech/youre-probably-wrong-about-caching/)
- [Pro Style Testing](https://msol.io/blog/tech/pro-style-testing/)
