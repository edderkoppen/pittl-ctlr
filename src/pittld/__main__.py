import argparse

import pittld
from pittld import logger
import pittld.driver
import pittld.inet
import pittld.lcd
import pittld.manager
import pittld.svc as svc


# Stage services and their mutually assured destruction
lcd = pittld.lcd.Service()
inet = pittld.inet.Service(lcd)
driver = pittld.driver.Service(lcd)
manager = pittld.manager.Service(driver)
svc.associate([lcd, inet, driver, manager])


def main():
    logger.info('Starting pittld {}'.format(pittld.__version__))

    lcd.start()
    inet.start()
    driver.start()
    manager.start()


if __name__ == '__main__':
    main()
