#!/usr/bin/env python
"""
Reads & Prints KISS frames from a Serial console.

For use with programs like Dire Wolf.
"""

import aprs
import kiss


def main():

    serial = aprs.SerialKISS("/dev/ttyUSB0", 115200)
    serial.start_no_config()
    serial.kiss_on()

    frame = aprs.APRSFrame.ui(
        destination="BEACON-2",
        source="DN5WA-11",
        path=["WIDE2-2"],
        info=b">Space Balloon 42",
    )
    frame = aprs.APRSFrame.from_str('DN5WA-11>APRS:>SPACE BALLOON 42')
    print(frame)

    serial.write(frame)


if __name__ == '__main__':

    main()
