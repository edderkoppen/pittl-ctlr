import argparse

import pittld.driver
import pittld.inet
import pittld.lcd
import pittld.manager
from pittld.svc import group


# Stage services and their mutually assured destruction
lcd = pittld.lcd.Service()
inet = pittld.inet.Service(lcd)
driver = pittld.driver.Service(lcd)
manager = pittld.manager.Service(driver)
group([lcd, inet, driver, manager])


def main():
    lcd.start()
    inet.start()
    driver.start()
    manager.start()


if __name__ == '__main__':
    main()
