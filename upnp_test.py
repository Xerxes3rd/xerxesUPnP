#!/usr/bin/env python

import xerxesUPnP
import signal
import sys
import time

upnp = None

upnpPortMappings = {
    ('UDP',  7980, 'DreamPi AFO'),
    ('UDP',  9789, 'DreamPi ChuChu'),
    ('BOTH', 3512, 'DreamPi Tetris'),
    ('UDP',  6500, 'DreamPi PBA SL'),
    ('TCP', 47624, 'DreamPi PBA SL'),
    ('UDP', 13139, 'DreamPi PBA SL'),
    ('UDP',  7648, 'DreamPi PR'),
    ('UDP',  1285, 'DreamPi PR'),
    ('UDP',  1028, 'DreamPi PR'),
}
upnpPortRangeMappings = {
    ('BOTH', 2300, 2400, 'DreamPi PBA SL'),
}

def signal_handler(signal, frame):
    print 'Exiting...'
    global upnp
    if upnp:
        upnp.stopThreads()
    sys.exit(0)

def doPortMapping(ip, add):
    global upnp, upnpPortMappings, upnpPortRangeMappings
    index = upnp.findRouterIndex()
    #index = 0
    # resp = self.sendReq(index, 'WANConnectionDevice', 'WANIPConnection', 'GetExternalIPAddress', {})
    # print resp

    if index >= 0:
        for entry in upnpPortMappings:
            if add:
                upnp.addPortMapping(index, entry[0], entry[1], entry[1], ip, entry[2])
            else:
                upnp.delPortMapping(index, entry[0], entry[1])

        for entry in upnpPortRangeMappings:
            start = entry[1]
            end = entry[2]
            while start <= end:
                if add:
                    upnp.addPortMapping(index, entry[0], start, start, ip, entry[2])
                else:
                    upnp.delPortMapping(index, entry[0], start)
                start = start + 1

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    upnp = xerxesUPnP.xerxesUPnP()
    upnp.startThreads()

    time.sleep(5)
    doPortMapping('192.168.1.98', True)
    time.sleep(1)
    doPortMapping('192.168.1.98', False)

    #for t in upnp.THREADS:
    #    t.join(1)

    while True:
        time.sleep(0.5)