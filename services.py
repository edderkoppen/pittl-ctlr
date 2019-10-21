import pittl.cli_server
import pittl.driver
import pittl.inet
import pittl.lcd


lcd_svc = pittl.lcd.Service()
inet_svc = pittl.inet.Service(lcd_svc)
driver_svc = pittl.driver.Service(lcd_svc)
cli_server_svc = pittl.cli_server.Service()


def start():
    lcd_svc.start()
    inet_svc.start()
    driver_svc.start()
    cli_server_svc.start()
