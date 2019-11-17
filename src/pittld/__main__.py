import argparse

import pittld.driver
import pittld.inet
import pittld.lcd
import pittld.manager
from pittld.svc import group


# Stage services and their mutually assured destruction
lcd = pittl.lcd.Service()
inet = pittl.inet.Service(lcd)
driver = pittl.driver.Service(lcd)
manager = pittl.manager.Service(driver)
group([lcd, inet, driver, manager])


def main():
    lcd.start()
    inet.start()
    driver.start()
    manager.start()


if __name__ == '__main__':
    main()
