#!/usr/bin/python
 

import time
 
import spidev


class MCP23S17(object):
    """This class provides an abstraction of the GPIO expander MCP23S17
    for the Raspberry Pi.
    It is depndent on the Python packages spidev and RPi.GPIO, which can
    be get from https://pypi.python.org/pypi/RPi.GPIO/0.5.11 and
    https://pypi.python.org/pypi/spidev.
    """
    PULLUP_ENABLED = 0
    PULLUP_DISABLED = 1

    DIR_INPUT = 0
    DIR_OUTPUT = 1

    LEVEL_LOW = 0
    LEVEL_HIGH = 1

    """Register addresses as documentined in the technical data sheet at
    http://ww1.microchip.com/downloads/en/DeviceDoc/21952b.pdf
    """
    MCP23S17_IODIRA = 0x00
    MCP23S17_IODIRB = 0x01
    MCP23S17_IPOLA = 0x2
    MCP23S17_IPOLB = 0x3
    MCP23S17_GPIOA = 0x12
    MCP23S17_GPIOB = 0x13
    MCP23S17_OLATA = 0x14
    MCP23S17_OLATB = 0x15
    MCP23S17_IOCON = 0x0A
    MCP23S17_GPPUA = 0x0C
    MCP23S17_GPPUB = 0x0D

    """Bit field flags as documentined in the technical data sheet at
    http://ww1.microchip.com/downloads/en/DeviceDoc/21952b.pdf
    """
    IOCON_UNUSED = 0x01
    IOCON_INTPOL = 0x02
    IOCON_ODR = 0x04
    IOCON_HAEN = 0x08
    IOCON_DISSLW = 0x10
    IOCON_SEQOP = 0x20
    IOCON_MIRROR = 0x40
    IOCON_BANK_MODE = 0x80

    IOCON_INIT = IOCON_SEQOP | IOCON_HAEN  # 0x28  # IOCON_SEQOP and IOCON_HAEN from above

    MCP23S17_CMD_WRITE = 0x40
    MCP23S17_CMD_READ = 0x41

    def __init__(self,   pin_reset=-1, device_id=0x00):
        """
        Constructor
        Initializes all attributes with 0.

        Keyword arguments:
        device_id -- The device ID of the component, i.e., the hardware address (default 0)
        pin_cs -- The Chip Select pin of the MCP, default 0
        pin_reset -- The Reset pin of the MCP
        """
        self.device_id = device_id
        self._GPIOA = 0
        self._GPIOB = 0
        self._IODIRA = 0
        self._IODIRB = 0
        self._GPPUA = 0
        self._GPPUB = 0
        self._pin_reset = pin_reset 
        self._spimode = 0b00
        self._spi = spidev.SpiDev()
        self.isInitialized = False

    def open(self):
        """Initializes the MCP23S17 with hardware-address access
        and sequential operations mode.
        """ 
        self._spi.open(0,0)

        self.max_speed_hz = 10000000
        self._spi.max_speed_hz = self.max_speed_hz
        self.isInitialized = True
        self._writeRegister(MCP23S17.MCP23S17_IOCON, MCP23S17.IOCON_INIT)

        # set defaults
        for index in range(0, 15):
            self.setDirection(index, MCP23S17.DIR_INPUT)
            self.setPullupMode(index, MCP23S17.PULLUP_ENABLED)

    def close(self):
        """Closes the SPI connection that the MCP23S17 component is using.
        """
        self._spi.close()
        self.isInitialized = False

    def setPullupMode(self, pin, mode):
        """Enables or disables the pull-up mode for input pins.

        Parameters:
        pin -- The pin index (0 - 15)
        mode -- The pull-up mode (MCP23S17.PULLUP_ENABLED, MCP23S17.PULLUP_DISABLED)
        """

        assert pin < 16
        assert (mode == MCP23S17.PULLUP_ENABLED) or (mode == MCP23S17.PULLUP_DISABLED)
        assert self.isInitialized

        if pin < 8:
            register = MCP23S17.MCP23S17_GPPUA
            data = self._GPPUA
            noshifts = pin
        else:
            register = MCP23S17.MCP23S17_GPPUB
            noshifts = pin & 0x07
            data = self._GPPUB

        if mode == MCP23S17.PULLUP_ENABLED:
            data |= (1 << noshifts)
        else:
            data &= (~(1 << noshifts))

        self._writeRegister(register, data)

        if pin < 8:
            self._GPPUA = data
        else:
            self._GPPUB = data

    def setDirection(self, pin, direction):
        """Sets the direction for a given pin.

        Parameters:
        pin -- The pin index (0 - 15)
        direction -- The direction of the pin (MCP23S17.DIR_INPUT, MCP23S17.DIR_OUTPUT)
        """

        assert (pin < 16)
        assert ((direction == MCP23S17.DIR_INPUT) or (direction == MCP23S17.DIR_OUTPUT))
        assert self.isInitialized

        if pin < 8:
            register = MCP23S17.MCP23S17_IODIRA
            data = self._IODIRA
            noshifts = pin
        else:
            register = MCP23S17.MCP23S17_IODIRB
            noshifts = pin & 0x07
            data = self._IODIRB

        if direction == MCP23S17.DIR_INPUT:
            data |= (1 << noshifts)
        else:
            data &= (~(1 << noshifts))

        self._writeRegister(register, data)

        if (pin < 8):
            self._IODIRA = data
        else:
            self._IODIRB = data

    def digitalRead(self, pin):
        """Reads the logical level of a given pin.

        Parameters:
        pin -- The pin index (0 - 15)
        Returns:
         - MCP23S17.LEVEL_LOW, if the logical level of the pin is low,
         - MCP23S17.LEVEL_HIGH, otherwise.
        """

        assert self.isInitialized
        assert (pin < 16)

        if pin < 8:
            self._GPIOA = self._readRegister(MCP23S17.MCP23S17_GPIOA)
            if (self._GPIOA & (1 << pin)) != 0:
                return MCP23S17.LEVEL_HIGH
            else:
                return MCP23S17.LEVEL_LOW
        else:
            self._GPIOB = self._readRegister(MCP23S17.MCP23S17_GPIOB)
            pin &= 0x07
            if (self._GPIOB & (1 << pin)) != 0:
                return MCP23S17.LEVEL_HIGH
            else:
                return MCP23S17.LEVEL_LOW

    def digitalWrite(self, pin, level):
        """Sets the level of a given pin.
        Parameters:
        pin -- The pin index (0 - 15)
        level -- The logical level to be set (LEVEL_LOW, LEVEL_HIGH)
        """

        assert self.isInitialized
        assert (pin < 16)
        assert (level == MCP23S17.LEVEL_HIGH) or (level == MCP23S17.LEVEL_LOW)

        if pin < 8:
            register = MCP23S17.MCP23S17_GPIOA
            data = self._GPIOA
            noshifts = pin
        else:
            register = MCP23S17.MCP23S17_GPIOB
            noshifts = pin & 0x07
            data = self._GPIOB

        if level == MCP23S17.LEVEL_HIGH:
            data |= (1 << noshifts)
        else:
            data &= (~(1 << noshifts))

        self._writeRegister(register, data)

        if (pin < 8):
            self._GPIOA = data
        else:
            self._GPIOB = data

    def writeGPIO(self, data):
        """Sets the data port value for all pins.
        Parameters:
        data - The 16-bit value to be set.
        """

        assert self.isInitialized

        self._GPIOA = (data & 0xFF)
        self._GPIOB = (data >> 8)
        self._writeRegisterWord(MCP23S17.MCP23S17_GPIOA, data)

    def readGPIO(self):
        """Reads the data port value of all pins.
        Returns:
         - The 16-bit data port value
        """

        assert self.isInitialized
        data = self._readRegisterWord(MCP23S17.MCP23S17_GPIOA)
        self._GPIOA = (data & 0xFF)
        self._GPIOB = (data >> 8)
        return data

    def _writeRegister(self, register, value):
        assert self.isInitialized
        command = MCP23S17.MCP23S17_CMD_WRITE | (self.device_id << 1)
        self._setSpiMode(self._spimode)
        self._spi.xfer2([command, register, value])

    def _readRegister(self, register):
        assert self.isInitialized
        command = MCP23S17.MCP23S17_CMD_READ | (self.device_id << 1)
        self._setSpiMode(self._spimode)
        data = self._spi.xfer2([command, register, 0])
        return data[2]

    def _readRegisterWord(self, register):
        assert self.isInitialized
        buffer = [0, 0]
        buffer[0] = self._readRegister(register)
        buffer[1] = self._readRegister(register + 1)
        return (buffer[1] << 8) | buffer[0]

    def _writeRegisterWord(self, register, data):
        assert self.isInitialized
        self._writeRegister(register, data & 0xFF)
        self._writeRegister(register + 1, data >> 8)
 
    def _setSpiMode(self, mode):
        if self._spi.mode != mode:
            self._spi.mode = mode
            self._spi.xfer2([0])  # dummy write, to force CLK to correct level


if __name__ == '__main__':
    """The following demo periodically toggles the level of
    all pins of two MCP23S17 conponents.
    """

     
    import time

    # you might also want to use the parameters bus, pin_cs, or pin_reset
    # to match your hardware setup
    mcp1 = MCP23S17(device_id=0x00)
    mcp2 = MCP23S17(device_id=0x01)
    mcp3 = MCP23S17(device_id=0x02)
    mcp1.open()
    mcp2.open()
    mcp3.open()
    delay = 0.1
    for x in range(0, 16):
        mcp1.setDirection(x, MCP23S17.DIR_OUTPUT)
        mcp2.setDirection(x, MCP23S17.DIR_OUTPUT)
        mcp3.setDirection(x, MCP23S17.DIR_OUTPUT)

    print("Starting blinky on all pins (CTRL+C to quit)")
    while (True):
        for x in range(0, 15):
            mcp1.digitalWrite(x, MCP23S17.LEVEL_HIGH) 
            time.sleep(delay)
        for x in range(0, 15):
            mcp2.digitalWrite(x, MCP23S17.LEVEL_HIGH) 
            time.sleep(delay)
        for x in range(0, 15):
            mcp3.digitalWrite(x, MCP23S17.LEVEL_HIGH) 
            time.sleep(delay)

        for x in range(0, 15):
            mcp1.digitalWrite(x, MCP23S17.LEVEL_LOW) 
            time.sleep(delay)
        for x in range(0, 15):
            mcp2.digitalWrite(x, MCP23S17.LEVEL_LOW) 
            time.sleep(delay)
        for x in range(0, 15):
            mcp3.digitalWrite(x, MCP23S17.LEVEL_LOW) 
            time.sleep(delay)