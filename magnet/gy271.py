import smbus2
from time import sleep
import math

C_REG_A = 0x09 # Address of Configuration register A
C_REG_B = 0x0a # Address of configuration register B
SR_period_REG = 0x0b # Address of SER/RESET register

MODE_STBY = 0x00 # standby mode
MODE_CONT = 0x01 # continous mode

ODR_10Hz = 0x00 # output data rate 10Hz
ODR_50Hz = 0x01 # output data rate 50Hz
ODR_100Hz = 0x10 # output data rate 100Hz
ODR_200Hz = 0x11 # output data rate 200Hz

SENS_2G = 0x00 # magnetic field sensitivity 2G
SENS_8G = 0x01 # magnetic field sensitivity 8G

OSR_512 = 0x00 # oversampling rate 512
OSR_256 = 0x01 # oversampling rate 256
OSR_128 = 0x10 # oversampling rate 128
OSR_64 = 0x11 # oversampling rate 64

X_axis_H = 0x00 # Address of X-axis MSB data register
Z_axis_H = 0x02 # Address of Z-axis MSB data register
Y_axis_H = 0x04 # Address of Y-axis MSB data register
TEMP_REG = 0x07 # Address of Temperature MSB data register

# declination angle of location where measurement going to be done
CURR_DECL = -0.00669 # determine by yourself
pi = 3.14159265359 # define pi value

class compass():
    def __init__(self, bus, address=0x0d, mode=MODE_CONT, odr=ODR_10Hz, sens=SENS_2G, osr=OSR_512, d=CURR_DECL):
        self.bus = smbus2.SMBus(bus)
        self.device_address = address # magnetometer device i2c address
        self._declination = d
        self.magnetometer_init(mode, odr, sens, osr)
        self.x, self.y, self.z = 0, 0, 0
        sleep(2)

    def soft_reset(self):
        self.bus.write_byte_data(self.device_address, C_REG_B, 0x80)

    def __set_mode(self, mode, odr, sens, osr):
        value = mode | odr  | sens | osr
        return value

    def magnetometer_init(self, mode, odr, sens, osr):
        self.soft_reset()

        self._mode = self.__set_mode(mode, odr, sens, osr)

        # Write to Configuration Register B: normal 0x00, soft_reset: 0x80
        self.bus.write_byte_data(self.device_address, C_REG_B, 0x00)
        
        # SET/RESET period set to 0x01 (recommendation from datasheet)
        self.bus.write_byte_data(self.device_address, SR_period_REG, 0x01)
        
        # write to Configuration Register A: mode
        self.bus.write_byte_data(self.device_address, C_REG_A, self._mode)

    def __read_raw_data(self, reg_address):
        # Read raw 16-bit value
        low_byte = self.bus.read_byte_data(self.device_address, reg_address)
        high_byte = self.bus.read_byte_data(self.device_address, reg_address + 1)

        # concatenate high_byte and low_byte into two_byte data
        value = (high_byte << 8) | low_byte
        
        if value > 32767:
            value = value - 65536
            
        return value

    def get_bearing(self):
        # Read Accelerometer raw value
        self.x = self.__read_raw_data(X_axis_H)
        self.z = self.__read_raw_data(Z_axis_H)
        self.y = self.__read_raw_data(Y_axis_H)
        
        heading = math.atan2(self.y, self.x) + self._declination
        
        # due to declination check for >360 degree
        if(heading > 2.0 * pi):
            heading = heading - 2.0 * pi
        
        # check for sign
        if(heading < 0.0):
            heading = heading + 2.0 * pi
        
        # convert into angle
        heading_angle = int(heading * 180.0 / pi)    
        return heading_angle

    def read_temp(self):
        low_byte = self.bus.read_byte_data(self.device_address, TEMP_REG)
        high_byte = self.bus.read_byte_data(self.device_address, TEMP_REG + 1)

        # concatenate higher and lower value
        value = (high_byte << 8) | low_byte # signed int (-32766 : 32767)
        value = value & 0x3fff # to get only positive numbers (first bit, sign bit)
        value = value / 520.0 # around: 125 (temp range) times 100 LSB/*C ~ 520
        return value

    def set_declination(self, value):
        self._declination = value
