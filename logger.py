import logging;

def init(configDict):
	logger = logging.getLogger();
	logger.setLevel(logging.INFO);	

	fh = logging.FileHandler(configDict['log']);
	formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s');
	fh.setFormatter(formatter);

	logger.addHandler(fh);

	return logger;

def write(logger,level,message):
	if (level == "info"):
		logger.info(message);
	elif (level == "debug"):
		logger.debug(message);
	elif (level == "error"):
		logger.error(message);		


