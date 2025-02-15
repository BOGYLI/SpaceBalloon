import struct
from smbus2 import SMBus, i2c_msg


# -----------------------------
# Modbus CRC16 calculation
# -----------------------------
def modbus_crc16(data):
    """Compute the standard Modbus CRC16 over a list of byte values."""
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

# -----------------------------
# Build Modbus request frames
# -----------------------------
def modbus_build_read_request(slave_addr, start_addr, count):
    """
    Build a Modbus RTU read-holding-registers request.
    The payload (sent over I²C) is:
      [Function Code, StartAddr_H, StartAddr_L, Count_H, Count_L, CRC_L, CRC_H]
    (CRC is computed with the unshifted slave address prepended.)
    """
    payload = [
        0x03,  # function code for reading holding registers
        (start_addr >> 8) & 0xFF,
        start_addr & 0xFF,
        (count >> 8) & 0xFF,
        count & 0xFF,
    ]
    crc_input = [slave_addr] + payload
    crc = modbus_crc16(crc_input)
    payload.append(crc & 0xFF)         # CRC low byte
    payload.append((crc >> 8) & 0xFF)    # CRC high byte
    return payload

def modbus_build_write_request(slave_addr, register_addr, value):
    """
    Build a Modbus write single register (function 0x06) request.
    The payload (sent over I²C) is:
      [Function Code, RegAddr_H, RegAddr_L, Value_H, Value_L, CRC_L, CRC_H]
    """
    payload = [
        0x06,  # function code for write single register
        (register_addr >> 8) & 0xFF,
        register_addr & 0xFF,
        (value >> 8) & 0xFF,
        value & 0xFF,
    ]
    crc_input = [slave_addr] + payload
    crc = modbus_crc16(crc_input)
    payload.append(crc & 0xFF)
    payload.append((crc >> 8) & 0xFF)
    return payload

# -----------------------------
# I²C Modbus read/write functions using smbus2 (repeated START)
# -----------------------------
def modbus_read_registers(bus, device_addr, start_addr, count):
    """
    Send a Modbus read (function 0x03) request over I²C and return a list of registers.
    Each register is 16 bits.
    
    The expected response payload is:
      [Function Code, Byte Count, Data Bytes..., CRC_L, CRC_H]
    """
    request = modbus_build_read_request(device_addr, start_addr, count)
    expected_length = count * 2 + 4  # Function(1)+ByteCount(1)+Data(count*2)+CRC(2)
    
    write_msg = i2c_msg.write(device_addr, request)
    read_msg = i2c_msg.read(device_addr, expected_length)
    bus.i2c_rdwr(write_msg, read_msg)
    
    response = list(read_msg)
    # Verify the CRC using the unshifted slave address prepended.
    crc_input = [device_addr] + response[:-2]
    crc_calculated = modbus_crc16(crc_input)
    crc_received = response[-2] | (response[-1] << 8)
    if crc_calculated != crc_received:
        print("CRC error on read (calculated 0x%04X vs received 0x%04X)" %
              (crc_calculated, crc_received))
        return None

    byte_count = response[1]
    if byte_count != count * 2:
        print("Byte count error: expected %d, got %d" % (count * 2, byte_count))
        return None

    # Parse registers (each register is big-endian)
    registers = []
    data_bytes = response[2:2 + byte_count]
    for i in range(0, len(data_bytes), 2):
        reg = (data_bytes[i] << 8) | data_bytes[i + 1]
        registers.append(reg)
    return registers

def modbus_write_register(bus, device_addr, register_addr, value):
    """
    Send a Modbus write single register (function 0x06) request over I²C.
    Returns True if the echoed response is received (or if the echo is all 0xFF, which we treat as success).
    """
    request = modbus_build_write_request(device_addr, register_addr, value)
    expected_length = 7  # Echo should be: Function(1)+Addr(2)+Value(2)+CRC(2) = 7 bytes

    write_msg = i2c_msg.write(device_addr, request)
    read_msg = i2c_msg.read(device_addr, expected_length)
    bus.i2c_rdwr(write_msg, read_msg)
    
    response = list(read_msg)
    # If the response is all 0xFF, assume the sensor is acknowledging the write.
    if all(b == 0xFF for b in response):
        print("Write echo returned 0xFF bytes, assuming success.")
        return True

    crc_input = [device_addr] + response[:-2]
    crc_calculated = modbus_crc16(crc_input)
    crc_received = response[-2] | (response[-1] << 8)
    if crc_calculated != crc_received:
        print("CRC error on write echo (calculated 0x%04X vs received 0x%04X)" %
              (crc_calculated, crc_received))
        return False
    return True

# -----------------------------
# Helper to decode a float from two registers
# -----------------------------
def registers_to_float(regs):
    """
    Convert two 16-bit registers (list of two integers) into a 32-bit IEEE-754 float.
    The sensor encodes the float with the two registers swapped:
      Byte1 = High byte of Register 2,
      Byte2 = Low byte of Register 2,
      Byte3 = High byte of Register 1,
      Byte4 = Low byte of Register 1.
    """
    if len(regs) != 2:
        raise ValueError("Expected 2 registers to decode a float.")
    packed = struct.pack('>HH', regs[1], regs[0])
    return struct.unpack('>f', packed)[0]
