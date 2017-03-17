"""Reverse proxy for Next Bus server."""
import argparse
import logging
import re
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


def parse_config(cmdline_opts):
    """Parse configuration from commmand line."""
    cmdline_opts.add_argument(
        '-p', '--port', help='Enter port number', default=8001)
    cmdline_opts.add_argument(
        '--host', help='Enter host name', default='localhost')
    cmdline_opts.add_argument(
        '-c', '--config', help='Enter config file', default='config.json')


def request_handler(epoll_context, parameters):
    """Application level request handler."""
    start_time = time.time()
    request, _, _ = epoll_context
    config_dict, redis_pool = parameters

    try:
        route, query_url, gzip_flag = get_route(request, config_dict)

        if query_url == "":
            json_response = _default_response_

        elif query_url == "stats":
            json_response = _simpledb.show()
        else:
            response = _cache.get_route(
                redis_pool, route, config_dict['redis_timeout'])
            if response == -1:
                xml_response = requests.get(query_url)
                json_response, dict_response = _utilities.to_json(
                    xml_response.text, "xml")
                print json_response
                try:
                    init_response = dict_response['body'][
                        'Error']['@shouldRetry'] == 'false'
                    error_cause = dict_response['body']['Error']['#text']
                    if init_response:
                        error_msg = ("Incorrect request: %s" % route)
                    else:
                        error_msg = (
                            "Server has not initalized, retry %s" % route)
                    logger.error(error_msg)
                    ex_resp, headers = to_gzip_response(error_msg, False)
                    return[400, headers, ex_resp + "\n" + error_cause]
                except:
                    _cache.set_route(redis_pool, route, dict_response)
            else:
                json_response, _ = _utilities.to_json(response, "dict")

        json_response, headers = to_gzip_response(json_response, gzip_flag)

        elapsed_time = time.time() - start_time
        if query_url != "stats" or query_url != "":
            _simpledb.update(elapsed_time, route, config_dict)

        logger.info("%s took %fs" % (route, elapsed_time))

        return [200, headers, str(json_response)]

    except Exception as e:
        ex_resp, headers = to_gzip_response(_default_response_, False)
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

    if route == "/":
        return [route, "", gzip_flag]

    short = ""
    if str(routers[-1]) == 'useShortTitles':
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
    if query == "stats":
        return "stats"
    elif query == "agencyList":
        return query_url + "agencyList"

    for i in range(index, len(routers), 1):
        try:
            last_query_point = str(query_points[i - index])
        except:
            pass
        query_url += last_query_point + str(routers[i])

    return query_url


def to_gzip_response(response, gzip_flag):
    """Return gzip compliant response and headers."""
    headers = "Content-Type: application/json\r\n"
    if gzip_flag:
        out = StringIO.StringIO()
        with gzip.GzipFile(fileobj=out, mode="w") as f:
            f.write(response)
        headers += "Vary: Accept-Encoding\r\n"
        headers += "Content-Encoding: gzip\r\n\r\n"
        response = out.getvalue()
        del out
    else:
        headers += "\r\n"
    return [response, headers]


if __name__ == '__main__':
    cmdline_opts = argparse.ArgumentParser(description=__description__)
    parse_config(cmdline_opts)
    args = cmdline_opts.parse_args()

    config_dict = _utilities.load_config(args.config)
    _utilities.init_logger(logger, config_dict)
    redis_pool = _cache.init(config_dict)

    this_server = epoll.Server(int(args.port), args.host, request_handler, [
                               config_dict, redis_pool])
    this_server.run()
