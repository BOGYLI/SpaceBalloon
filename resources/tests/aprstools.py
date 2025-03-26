import re
import math
from aprslib import base91
from aprslib.exceptions import ParseError
from aprslib.parsing.common import parse_dao
from aprslib.parsing.telemetry import parse_comment_telemetry


MTYPE_TABLE_STD = {
    "111": "M0: Off Duty",
    "110": "M1: En Route",
    "101": "M2: In Service",
    "100": "M3: Returning",
    "011": "M4: Committed",
    "010": "M5: Special",
    "001": "M6: Priority",
    "000": "Emergency",
    }
MTYPE_TABLE_CUSTOM = {
    "111": "C0: Custom-0",
    "110": "C1: Custom-1",
    "101": "C2: Custom-2",
    "100": "C3: Custom-3",
    "011": "C4: Custom-4",
    "010": "C5: Custom-5",
    "001": "C6: Custom-6",
    "000": "Emergency",
    }


# KISS protocol
KISS_FEND = b'\xC0'
KISS_FESC = b'\xDB'
KISS_TFEND = b'\xDC'
KISS_TFESC = b'\xDD'
KISS_DATA_FRAME = b'\x00'


def to_hex_bytes(data):
    """Converts data to hex bytes for display purposes."""

    return " ".join(f"0x{data.hex()[i:i+2]}" for i in range(0, len(data.hex()), 2))


def kiss_escape(data):
    """Escape special KISS characters in data."""

    data = data.replace(KISS_FEND, KISS_FESC + KISS_TFEND)
    data = data.replace(KISS_FESC, KISS_FESC + KISS_TFESC)
    return data


def kiss_unescape(data):
    """Unescape KISS special characters in data."""
    data = data.replace(KISS_FESC + KISS_TFEND, KISS_FEND)
    data = data.replace(KISS_FESC + KISS_TFESC, KISS_FESC)
    return data


def construct_kiss_frame(aprs_packet):
    """Construct a KISS frame for an APRS packet."""

    kiss_frame = KISS_DATA_FRAME + aprs_packet
    kiss_frame = kiss_escape(kiss_frame)
    return KISS_FEND + kiss_frame + KISS_FEND


def encode_gps_aprs(lat, lon):
    """Converts latitude and longitude to APRS format."""

    # Convert latitude to APRS format
    lat_deg = int(lat)
    lat_min = (lat - lat_deg) * 60
    lat_hemi = 'N' if lat >= 0 else 'S'
    aprs_lat = f'{abs(lat_deg):02d}{lat_min:05.2f}{lat_hemi}'

    # Convert longitude to APRS format
    lon_deg = int(lon)
    lon_min = (lon - lon_deg) * 60
    lon_hemi = 'E' if lon >= 0 else 'W'
    aprs_lon = f'{abs(lon_deg):03d}{lon_min:05.2f}{lon_hemi}'

    return aprs_lat, aprs_lon


def decode_gps_aprs(coord_str, degrees_pos=2):
    """Convert latitude/longitude from APRS format to decimal degrees."""

    match = re.match(r'(\d{' + str(degrees_pos) + r'})(\d{2}\.\d+)([NSEW])', coord_str)

    if match:
        degrees = int(match.group(1))  # Degrees part
        minutes = float(match.group(2))  # Minutes part
        direction = match.group(3)  # N/S/E/W

        decimal_degrees = degrees + minutes / 60
        if direction in 'SW':  # South or West, make negative
            decimal_degrees *= -1

        return decimal_degrees


def encode_ax25_address(call, ssid, is_last=False):
    """Encodes a callsign and SSID into the AX.25 address format."""

    address = []
    
    # Callsign must be 6 characters long, pad with spaces if necessary
    call = call.ljust(6)
    
    # Shift left by 1 bit (as per AX.25 address field encoding)
    for char in call:
        address.append(ord(char) << 1)
    
    # Encode SSID correctly, bits 1-4 contain the SSID, bit 5 is always 1, and bits 6-7 are reserved
    ssid_byte = 0b01100000 | (ssid << 1)  # Bit 5 is set to 1, bits 6 and 7 are 0

    if is_last:
        ssid_byte |= 0b00000001  # Set the last bit to 1 for the last address field

    address.append(ssid_byte)
    
    return address


def encode_ax25_frame(source_call, source_ssid, dest_call, dest_ssid, information):
    """Constructs an AX.25 UI frame using the provided parameters."""
    
    # AX.25 control field for UI frame is always 0x03
    control_field = 0x03
    
    # Protocol ID for no layer 3 is 0xF0 (used in APRS, etc.)
    protocol_id = 0xF0
    
    # Encode the source and destination addresses
    dest_address = encode_ax25_address(dest_call, dest_ssid)
    source_address = encode_ax25_address(source_call, source_ssid)
    path1_address = encode_ax25_address("WIDE1", 1)
    path2_address = encode_ax25_address("WIDE2", 2, True)
    
    # Combine the frame components
    frame = dest_address + source_address + path1_address + path2_address
    
    # Append the control and protocol ID fields
    frame += [control_field, protocol_id]
    
    # Append the information field (message)
    frame += [ord(c) for c in information]
    
    # Convert to byte array
    frame_bytes = bytearray(frame)
    
    return frame_bytes


def decode_ax25_frame(frame):
    """Extracts the source, destination, path, and message from an AX.25 frame."""

    try:
        # Extract destination callsign (first 7 bytes)
        dest_call = "".join([chr(b >> 1) for b in frame[0:6]]).strip()
        dest_ssid = (frame[6] >> 1) & 0x0F
        dest_full = f"{dest_call}-{dest_ssid}"

        # Extract source callsign (next 7 bytes)
        source_call = "".join([chr(b >> 1) for b in frame[7:13]]).strip()
        source_ssid = (frame[13] >> 1) & 0x0F
        source_full = f"{source_call}-{source_ssid}"

        # Extract digipeater path (each address is 7 bytes)
        path_start = 14
        path = []
        while not frame[path_start + 6] & 0x01:  # Check if this is the last address
            digi_call = "".join([chr(b >> 1) for b in frame[path_start:path_start + 6]]).strip()
            digi_ssid = (frame[path_start + 6] >> 1) & 0x0F
            path.append(f"{digi_call}-{digi_ssid}")
            path_start += 7

        # Add the final digipeater in the path
        last_digi_call = "".join([chr(b >> 1) for b in frame[path_start:path_start + 6]]).strip()
        last_digi_ssid = (frame[path_start + 6] >> 1) & 0x0F
        path.append(f"{last_digi_call}-{last_digi_ssid}")

        # Control and protocol fields are after the addresses
        message_start = path_start + 7 + 2  # Control field (1 byte) + protocol ID (1 byte)
        message = frame[message_start:].decode('ascii', errors='ignore')

        return source_full, dest_full, path, message

    except Exception as e:
        print(f"Failed to decode AX.25 frame: {e}")
        return None, None, None, None


def parse_mice(dstcall, body):
    parsed = {'format': 'mic-e'}

    dstcall = dstcall.split('-')[0]

    # verify mic-e format
    if len(dstcall) != 6:
        raise ParseError("dstcall has to be 6 characters")
    if len(body) < 8:
        raise ParseError("packet data field is too short")
    if not re.match(r"^[0-9A-Z]{3}[0-9L-Z]{3}$", dstcall):
        raise ParseError("invalid dstcall")

    # get symbol table and symbol
    parsed.update({
        'symbol': body[6],
        'symbol_table': body[7]
        })

    # parse latitude
    # the routine translates each characters into a lat digit as described in
    # 'Mic-E Destination Address Field Encoding' table
    tmpdstcall = ""
    for i in dstcall:
        if i in "KLZ":  # spaces
            tmpdstcall += " "
        elif ord(i) > 76:  # P-Y
            tmpdstcall += chr(ord(i) - 32)
        elif ord(i) > 57:  # A-J
            tmpdstcall += chr(ord(i) - 17)
        else:  # 0-9
            tmpdstcall += i

    # determine position ambiguity
    match = re.findall(r"^\d+( *)$", tmpdstcall)
    if not match:
        raise ParseError("invalid latitude ambiguity")

    posambiguity = len(match[0])
    parsed.update({
        'posambiguity': posambiguity
        })

    # adjust the coordinates be in center of ambiguity box
    tmpdstcall = list(tmpdstcall)
    if posambiguity > 0:
        if posambiguity >= 4:
            tmpdstcall[2] = '3'
        else:
            tmpdstcall[6 - posambiguity] = '5'

    tmpdstcall = "".join(tmpdstcall)

    latminutes = float(("%s.%s" % (tmpdstcall[2:4], tmpdstcall[4:6])).replace(" ", "0"))
    latitude = int(tmpdstcall[0:2]) + (latminutes / 60.0)

    # determine the sign N/S
    latitude = -latitude if ord(dstcall[3]) <= 0x4c else latitude

    parsed.update({
        'latitude': latitude
        })

    # parse message bits

    mbits = re.sub(r"[0-9L]", "0", dstcall[0:3])
    mbits = re.sub(r"[P-Z]", "1", mbits)
    mbits = re.sub(r"[A-K]", "2", mbits)

    parsed.update({
        'mbits': mbits
        })

    # resolve message type

    if mbits.find("2") > -1:
        parsed.update({
            'mtype': MTYPE_TABLE_CUSTOM[mbits.replace("2", "1")]
            })
    else:
        parsed.update({
            'mtype': MTYPE_TABLE_STD[mbits]
            })

    # parse longitude

    longitude = ord(body[0]) - 28  # decimal part of longitude
    longitude += 100 if ord(dstcall[4]) >= 0x50 else 0  # apply lng offset
    longitude += -80 if longitude >= 180 and longitude <= 189 else 0
    longitude += -190 if longitude >= 190 and longitude <= 199 else 0

    # long minutes
    lngminutes = ord(body[1]) - 28.0
    lngminutes += -60 if lngminutes >= 60 else 0

    # + (long hundredths of minutes)
    lngminutes += ((ord(body[2]) - 28.0) / 100.0)

    # apply position ambiguity
    # routines adjust longitude to center of the ambiguity box
    if posambiguity == 4:
        lngminutes = 30
    elif posambiguity == 3:
        lngminutes = (math.floor(lngminutes/10) + 0.5) * 10
    elif posambiguity == 2:
        lngminutes = math.floor(lngminutes) + 0.5
    elif posambiguity == 1:
        lngminutes = (math.floor(lngminutes*10) + 0.5) / 10.0
    elif posambiguity != 0:
        raise ParseError("Unsupported position ambiguity: %d" % posambiguity)

    longitude += lngminutes / 60.0

    # apply E/W sign
    longitude = 0 - longitude if ord(dstcall[5]) >= 0x50 else longitude

    parsed.update({
        'longitude': longitude
        })

    # parse speed and course
    speed = (ord(body[3]) - 28) * 10
    course = ord(body[4]) - 28
    quotient = int(course / 10.0)
    course += -(quotient * 10)
    course = course*100 + ord(body[5]) - 28
    speed += quotient

    speed += -800 if speed >= 800 else 0
    course += -400 if course >= 400 else 0

    speed *= 1.852  # knots * 1.852 = kmph
    parsed.update({
        'speed': speed,
        'course': course
        })

    # the rest of the packet can contain telemetry and comment

    if len(body) > 8:
        body = body[8:]

        # check for optional 2 or 5 channel telemetry
        match = re.findall(r"^('[0-9a-f]{10}|`[0-9a-f]{4})(.*)$", body)
        if match:
            hexdata, body = match[0]

            hexdata = hexdata[1:]             # remove telemtry flag
            channels = int(len(hexdata) / 2)  # determine number of channels
            hexdata = int(hexdata, 16)        # convert hex to int

            telemetry = []
            for i in range(channels):
                telemetry.insert(0, int(hexdata >> 8*i & 255))

            parsed.update({'telemetry': telemetry})

        # check for optional altitude
        match = re.findall(r"^(.*)([!-{]{3})\}(.*)$", body)
        if match:
            body, altitude, extra = match[0]

            altitude = base91.to_decimal(altitude) - 10000
            parsed.update({'altitude': altitude})

            body = body + extra

        # attempt to parse comment telemetry
        body, telemetry = parse_comment_telemetry(body)
        parsed.update(telemetry)

        # parse DAO extention
        body = parse_dao(body, parsed)

        # rest is a comment
        parsed.update({'comment': body.strip(' ')})

    return ('', parsed)

