# MicroPython SSD1306 OLED driver, I2C and SPI interfaces
# https://github.com/micropython/micropython-lib/blob/7128d423c2e7c0309ac17a1e6ba873b909b24fcc/micropython/drivers/display/ssd1306/ssd1306.py#L30%5D
# 2025-07-12 Modified to add
#    hwScrollOn|Off() h/w scrolling, select lines to scroll, left or right
#    rotate(True|False) rotate display 0/180 degrees - not amazingly useful for text!

from micropython import const
import framebuf
import logging

logger = logging.getLogger(__name__)
from ESPLogRecord import ESPLogRecord
logger.record = ESPLogRecord()

# register definitions
SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xA4)
SET_NORM_INV = const(0xA6)
SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xA0)
SET_MUX_RATIO = const(0xA8)
SET_COM_OUT_DIR = const(0xC0)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)
SET_HSCROLL_PARAMS = const(0x26)
SET_SCROLL_ON = const(0x2F)
SET_SCROLL_OFF = const(0x2E)


# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class SSD1306(framebuf.FrameBuffer):
    def __init__(self, width, height, external_vcc):
        logger.debug("SSD1306 Init W:%d H:%d Ext_VCC:%s", width, height, external_vcc)
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        self._scroll = False
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00,  # off
            # address setting
            SET_MEM_ADDR,
            0x00,  # horizontal
            # resolution and layout
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01,  # column addr 127 mapped to SEG0
            SET_MUX_RATIO,
            self.height - 1,
            SET_COM_OUT_DIR | 0x08,  # scan from COM[N] to COM0
            SET_DISP_OFFSET,
            0x00,
            SET_COM_PIN_CFG,
            0x02 if self.width > 2 * self.height else 0x12,
            # timing and driving scheme
            SET_DISP_CLK_DIV,
            0x80,
            SET_PRECHARGE,
            0x22 if self.external_vcc else 0xF1,
            SET_VCOM_DESEL,
            0x30,  # 0.83*Vcc
            # display
            SET_CONTRAST,
            0xFF,  # maximum
            SET_ENTIRE_ON,  # output follows RAM contents
            SET_NORM_INV,  # not inverted
            # charge pump
            SET_CHARGE_PUMP,
            0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01,
        ):  # on
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def rotate(self, rotate: bool) -> None:
        """Rotate the display 0 or 180 degrees"""
        self.write_cmd(SET_COM_OUT_DIR | ((rotate & 1) << 3))
        self.write_cmd(SET_SEG_REMAP | (rotate & 1))
        # com output (vertical mirror) is changed immediately
        # you need to call show() for the seg remap to be visible
        self.show() # Save the caller the trouble - we want it to be right

    def hwScrollOn(self, left, startLine, endLine, rate):
        ''' left - True|False,
            startLine - 0-7,
            endLine - 0-7, >= startLine,
            rate - 1-8; options are 256,128,64,25,5,4,3,2 frame interval
            
            Command bytes:
            0 Scroll + dir
            1 0x00
            2 start page
            3 frame rate interval
            4 end page
            5 0x00
            6 0xFF
        '''
        #                256 128 64  25  5   4   3   2
        rates = bytes(b'\x03\x02\x01\x06\x00\x05\x04\x07')
        if self._scroll:
            raise Exception("scrollOn called when already scrolling - call scrollOff first!")
        if (endLine < startLine) or (endLine < 0) or (startLine < 0) or (endLine > 7) or (startLine > 7):
            raise ValueError("startLine or endLine not 0-7 or end < start")
        if (rate > len(rates)) or (rate < 1):
            raise IndexError("rate must be 1 <= rate <= 8")
        self.write_cmd(SET_HSCROLL_PARAMS | (left & 1))
        self.write_cmd(0x00)
        self.write_cmd(startLine)
        self.write_cmd(rates[rate-1])
        self.write_cmd(endLine)
        self.write_cmd(0x00)
        self.write_cmd(0xFF)
        self._scroll = True
        self.write_cmd(SET_SCROLL_ON)

    def hwScrollOff(self):
        if self._scroll:
            self.write_cmd(SET_SCROLL_OFF)
        self._scroll = False
            
    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            # displays with width of 64 pixels are shifted by 32
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)


class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        logger.debug("SSD1306_I2C Init W:%d H:%d I2C:%s Addr:%d Ext_VCC:%s", width, height, i2c, addr, external_vcc)
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]  # Co=0, D/C#=1
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80  # Co=1, D/C#=0
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        self.write_list[1] = buf
        self.i2c.writevto(self.addr, self.write_list)


class SSD1306_SPI(SSD1306):
    def __init__(self, width, height, spi, dc, res, cs, external_vcc=False):
        logger.debug("SSD1306_SPI Init W:%d H:%d SPI:%s dc:%s Reset:%s CS:%s Ext_VCC:%s", width, height, spi, dc, res, cs, external_vcc)
        self.rate = 10 * 1024 * 1024
        dc.init(dc.OUT, value=0)
        res.init(res.OUT, value=0)
        cs.init(cs.OUT, value=1)
        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs
        import time

        self.res(1)
        time.sleep_ms(1)
        self.res(0)
        time.sleep_ms(10)
        self.res(1)
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)
