import logging
import sys


# Logging config
logger = logging.getLogger('pittl')
logger.setLevel(logging.INFO)

sh = logging.StreamHandler(sys.stdout)

fmt = '%(asctime)s - %(threadName)s [%(levelname)s] %(message)s'
formatter = logging.Formatter(fmt)

sh.setFormatter(formatter)

logger.addHandler(sh)
