import pittl.driver
import pittl.inet
import pittl.lcd
import pittl.manager


lcd = pittl.lcd.Service()
inet = pittl.inet.Service(lcd)
driver = pittl.driver.Service(lcd)
manager = pittl.manager.Service(driver)


def start():
    lcd.start()
    inet.start()
    driver.start()
    manager.start()
