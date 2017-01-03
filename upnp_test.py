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
    #('BOTH', 2300, 2400, 'DreamPi PBA SL'),
}

def signal_handler(signal, frame):
    print 'Exiting...'
    global upnp
    if upnp:
        upnp.stopThreads()
    sys.exit(0)

def runTests():
    global upnp
    upnp.showDeviceInfo(upnp.routerIndex)
    print upnp.sendReq(upnp.routerIndex, 'WANConnectionDevice', 'WANIPConnection', 'GetExternalIPAddress', {})
    upnp.doPortMapping('192.168.1.98', upnpPortMappings, upnpPortRangeMappings, True)
    upnp.showPortMappings(upnpPortMappings, upnpPortRangeMappings)
    time.sleep(1)
    upnp.doPortMapping('192.168.1.98', upnpPortMappings, upnpPortRangeMappings, False)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    timeoutSeconds = 30
    loop = True
    upnp = xerxesUPnP.xerxesUPnP()
    upnp.suppressMirandaSTDOUT = False
    upnp.startThreads()

    #time.sleep(10)

    #for t in upnp.THREADS:
    #    t.join(1)

    start = time.time()
    while loop:
        time.sleep(0.5)
        if (time.time() - start) > timeoutSeconds:
            print "Timed out finding WAN device"
            loop = False
        if upnp.routerIndex >= 0:
            print "Found router index, running tests"
            runTests()
            loop = False

    upnp.stopThreads()