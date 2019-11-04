import pittl.ctlr.driver
import pittl.ctlr.inet
import pittl.ctlr.lcd
import pittl.ctlr.manager


lcd = None
inet = None
driver = None
manager = None


def stage():
    global lcd, inet, driver, manager
    lcd = pittl.ctlr.lcd.Service()
    inet = pittl.ctlr.inet.Service(lcd)
    driver = pittl.ctlr.driver.Service(lcd)
    manager = pittl.ctlr.manager.Service(driver)


def start():
    if not lcd or not inet or not driver or not manager:
        stage()

    lcd.start()
    inet.start()
    driver.start()
    manager.start()


def stop():
    global lcd, inet, driver, manager
    del lcd, inet, driver, manager
