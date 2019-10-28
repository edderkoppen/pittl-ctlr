import pittl.cli.server
import pittl.driver
import pittl.inet
import pittl.lcd


lcd = pittl.lcd.Service()
inet = pittl.inet.Service(lcd)
driver = pittl.driver.Service(lcd)
cli_server = pittl.cli.server.Service(driver)


def start():
    lcd.start()
    inet.start()
    driver.start()
    cli_server.start()
