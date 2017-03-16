"""Basic utility functions."""
import json
import logging
import sys

import xmltodict


def load_config(path):
	"""Load config from json based file to dict."""
	try:
		with open(path, 'r') as f:
			config_dict = json.loads(f.read())
	except Exception as e:
		print ("Bad configuration file name %s %s" % (path, e))
		sys.exit(-1)
	return config_dict


def init_logger(logger, config_dict):
	"""Set a log format and defines log handleling."""
	logger.setLevel(logging.INFO)

	fh = logging.FileHandler(config_dict['log'])
	formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
	fh.setFormatter(formatter)

	logger.addHandler(fh)


def to_json(response, __type__):
	"""Convert responses to json data."""
	to_dict = dict()
	if __type__ == "xml":
		to_dict = xmltodict.parse(response)
	elif __type__ == "dict":
		to_dict = response
	response = json.dumps(to_dict, sort_keys=True, indent=4, separators=(",", ":"))
	return [response, to_dict]
