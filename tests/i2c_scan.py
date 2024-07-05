import smbus2

# Create an I2C bus instance
bus = smbus2.SMBus(1)  # 1 indicates /dev/i2c-1

def scan_i2c_bus():

    print("Scanning I2C bus for devices...")
    devices = []
    for address in range(0x03, 0x77):
        try:
            bus.write_quick(address)
            devices.append(hex(address))
        except IOError:
            pass
    if devices:
        print("I2C devices found at addresses:", devices)
    else:
        print("No I2C devices found")

if __name__ == "__main__":

    scan_i2c_bus()
