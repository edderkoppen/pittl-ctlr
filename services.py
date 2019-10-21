from enum import Enum

import pittl.main as main
import pittl.lcd as lcd
import pittl.inet as inet


lcd_service = lcd.Service()
inet_service = inet.Service(lcd_service)
main_service = main.Service()


def start():
    lcd_service.start()
    inet_service.start()
    main_service.start()
