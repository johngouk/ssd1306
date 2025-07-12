# SPI pins SCL 25 SDA 26
import ssd1306
import time, random, logging
from micropython import const
import asyncio
import random
import os, gc
from machine import Pin, I2C
import machine

machine.freq(240000000) # Juice things up a bit

#           ADJUST LOG LEVEL HERE->vvvvvv, values are DEBUG, INFO, WARNING, ERROR, FATAL
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)06d %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)
try:
    from ESPLogRecord import ESPLogRecord
    logger.record = ESPLogRecord()
except ImportError:
    print('Unable to import ESPLogRecord!!')
    pass

sda = Pin(26)    # data/command
scl = Pin(25)

logger.info("testSSD1306 starting...")
logger.info("testSSD1306: I2C: SCL:%s SDA:%s", scl, sda)
i2c = I2C(1, scl=scl, sda=sda)  # sck=25 (scl), mosi=26 (sda), miso=12 (unused)

logger.info("testSSD1306: Init display")
# width, height, I2C, addr, external_vcc
display = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

'''
logger.info("testSSD1306: Display text")
display.text('Hello, World!', 0, 0, 1)
display.show()
time.sleep(1)

logger.info("testSSD1306: MicroPython logo")
display.fill(0)
display.fill_rect(0, 0, 32, 32, 1)
display.fill_rect(2, 2, 28, 28, 0)
display.vline(9, 8, 22, 1)
display.vline(16, 2, 22, 1)
display.vline(23, 8, 22, 1)
display.fill_rect(26, 24, 2, 4, 1)
display.text('MicroPython', 40, 0, 1)
display.text('SSD1306', 40, 12, 1)
display.text('OLED 128x64', 40, 24, 1)
display.show()
time.sleep(2)
'''
'''
logger.info("testSSD1306: Lines of text 9 pixels high")
display.fill(0)
display.text('Line: 0, 0, 1', 0, 0, 1)
display.text('Line: 0, 9, 2', 0, 9, 2)
display.text('Line: 0, 18, 3', 0, 18, 3)
display.text('Line: 0, 27, 3', 0, 27, 4)
display.text('Line: 0, 36, 3', 0, 36, 5)
display.text('Line: 0, 45, 3', 0, 45, 6)
display.show()
time.sleep(2)
'''
#display.invert(1)
#display.show()
#time.sleep(2)

display.rotate(False)
#display.show()

#display.fill(1)
#display.show()
#time.sleep(2)
#display.rotate(True)

# Display can show 8 lines of 16 chars legibly

logger.info("testSSD1306: Lines of text 8 pixels high")
display.fill(0)
display.text('0123456789ABCDEFG', 0, 0, 1)
display.text('Line: 0, 8, 2', 0, 8, 2)
display.text('Line: 0, 16, 3', 0, 16, 3)
display.text('Line: 0, 24, 3', 0, 24, 4)
display.text('Line: 0, 32, 3', 0, 32, 5)
display.text('Line: 0, 40, 3', 0, 40, 6)
display.text('Line: 0, 48, 3', 0, 48, 6)
display.text('Line: 0, 56, 3', 0, 56, 6)
display.show()
time.sleep(2)


logger.info("testSSD1306: Lines of text 8 pixels high - h/w scrolling")
display.hwScrollOn(True, 2, 3, 8)
time.sleep(10)
display.hwScrollOff()
display.hwScrollOn(False, 2, 3, 8)
time.sleep(10)
display.hwScrollOff()


logger.info("testSSD1306: Lines of text 8 pixels high - framebuf scrolling")
display.scroll(64,0)
display.show()



'''
logger.info("testSSD1306: Test hwScrollOn/hwScrollOn no hwScrollOff exception")
display.hwScrollOn(True, 2, 3, 8)
display.hwScrollOn(True, 2, 3, 8)
'''
#display.invert(1)
#display.show()
#time.sleep(2)
#display.rotate(False)
#display.show()