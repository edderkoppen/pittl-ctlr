import logging
import sys


# Version
__version__ = '0.2.0'


# Logging config
logger = logging.getLogger('pittld')
logger.setLevel(logging.DEBUG)

sh = logging.StreamHandler(sys.stdout)

fmt = '%(asctime)s - %(threadName)s [%(levelname)s] %(message)s'
formatter = logging.Formatter(fmt)

sh.setFormatter(formatter)

logger.addHandler(sh)
