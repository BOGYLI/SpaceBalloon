#!/usr/bin/env python
"""
Reads & Prints KISS frames from a Serial console.

For use with programs like Dire Wolf.
"""

import aprs
import aprs.kiss_classes
import kiss


def main():
    frame = aprs.kiss_classes.Frame()
    frame.source = aprs.Callsign('DN5WA-11')
    frame.destination = aprs.Callsign('WX')
    frame.path = [aprs.Callsign('WIDE2-2')]
    frame.text = '>Space Balloon Test'

    ki = kiss.TCPKISS(host='192.168.178.95', port=1234)
    ki.start()
    ki.write(frame.encode_kiss())


if __name__ == '__main__':
    main()
