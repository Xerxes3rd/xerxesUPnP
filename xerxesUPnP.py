#!/usr/bin/env python

import miranda
import time
import asyncore
import threading
import base64
import sys
import os
from struct import unpack
#from socket import AF_INET, inet_pton
import socket

class AsyncoreSocketUDP(asyncore.dispatcher):

  dataRecv = None

  def __init__(self, sock):
    asyncore.dispatcher.__init__(self)
    asyncore.dispatcher.set_socket(self, sock)
    #self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
    #self.bind(('', port))
    #self.dataRecv = dataRecv
  # This is called every time there is something to read
  def handle_read(self):
    data = self.recv(2048)

    if self.dataRecv != None:
        self.dataRecv(data)
    # ... do something here, eg self.sendto(data, (addr, port))

  def writable(self):
    return False # don't want write notifies

class xerxesUPnP:
    THREADS = []
    run = False
    hp = None
    readThread = None
    searchThread = None
    suppressMirandaSTDOUT = True
    routerIndex = -1
    printPortMappingResponse = True

    def isPrivate(self, ip):
      f = unpack('!I', socket.inet_pton(socket.AF_INET, ip))[0]
      private = (
          [2130706432, 4278190080],  # 127.0.0.0,   255.0.0.0   http://tools.ietf.org/html/rfc3330
          [3232235520, 4294901760],  # 192.168.0.0, 255.255.0.0 http://tools.ietf.org/html/rfc1918
          [2886729728, 4293918720],  # 172.16.0.0,  255.240.0.0 http://tools.ietf.org/html/rfc1918
          [167772160, 4278190080],  # 10.0.0.0,    255.0.0.0   http://tools.ietf.org/html/rfc1918
      )
      for net in private:
          if (f & net[1]) == net[0]:
              return True
      return False

    # Actively search for UPNP devices
    def msearch(self, searchType, searchName):
        defaultST = "upnp:rootdevice"
        st = "schemas-upnp-org"

        if not searchType and not searchName:
            st = "urn:%s:%s:%s:%s" % (st, searchType, searchName, self.hp.UPNP_VERSION.split('.')[0])
        else:
            st = defaultST

        # Build the request
        request = "M-SEARCH * HTTP/1.1\r\n" \
                  "HOST:%s:%d\r\n" \
                  "ST:%s\r\n" % (self.hp.ip, self.hp.port, st)
        for header, value in self.hp.msearchHeaders.iteritems():
            request += header + ':' + value + "\r\n"
        request += "\r\n"

        last = 0

        while self.run:
            sys.stdout.flush()
            try:
                if time.time() - last > 5 and (self.hp.MAX_HOSTS == 0 or (self.hp.ENUM_HOSTS) < self.hp.MAX_HOSTS):
                    print "Searching for " + searchType + " devices...\n"
                    self.hp.send(request, self.hp.ssock)
                    last = time.time()

                time.sleep(0.2)

            except Exception, e:
                print '\nmsearch discover halted: ', e
                #break
        print 'msearch exit'

    def readSock(self):
        start = time.time()
        hostEntry = None
        previousName = ''

        while self.run:
            try:
                data = self.hp.recv(1024, self.hp.ssock)
                stdoutSuppressed = False

                if (data != None) and (data != False):
                    if self.suppressMirandaSTDOUT:
                        actualstdout = sys.stdout
                        sys.stdout = open(os.devnull,'w')
                        stdoutSuppressed = True
                    self.hp.parseSSDPInfo(data, False, False)
                    if stdoutSuppressed:
                        sys.stdout = actualstdout
                        sys.stdout.flush()

                    if self.routerIndex == -1:
                        self.routerIndex = self.findRouterIndex()
                        print "Router index is " + str(self.routerIndex)

                #index = self.findRouterIndex()

                #if index != -1:
                #    hostInfo = self.hp.ENUM_HOSTS[index]
                #    if hostInfo['name'] != previousName:
                #        self.doPortMapping(index)
                #        previousName = hostInfo['name']

            except Exception, e:
                print '\nreadSock error: ', e
                #break
        print 'readsock exit'

    def findRouterIndex(self):
        for index in self.hp.ENUM_HOSTS:
            self.requestDeviceInfo(index)
            hostInfo = self.hp.ENUM_HOSTS[index]
            if hostInfo['dataComplete'] == True:
                if 'WANConnectionDevice' in hostInfo['deviceList']:
                    resp = self.sendReq(index, 'WANConnectionDevice', 'WANIPConnection', 'GetExternalIPAddress', {})
                    hostInfo['NewExternalIPAddress'] = resp['NewExternalIPAddress']
                    hostInfo['IPAddress'] = str.split(hostInfo['name'], ':')[0]
                    #print hostInfo
                    if hostInfo['NewExternalIPAddress'] != hostInfo['IPAddress']:
                        if self.isPrivate(hostInfo['NewExternalIPAddress']):
                            print "Skipping host " + hostInfo['name'] + ": no public IP address"
                        else:
                            return index
        return -1

    def requestDeviceInfo(self, index):
        if index >= 0:
            hostInfo = self.hp.ENUM_HOSTS[index]
            if hostInfo['dataComplete'] == False:
                print "Requesting device and service info for %s (this could take a few seconds)..." % hostInfo['name']
                (xmlHeaders, xmlData) = self.hp.getXML(hostInfo['xmlFile'])
                if xmlData == False:
                    print 'Failed to request host XML file:', hostInfo['xmlFile']
                    return
                if self.hp.getHostInfo(xmlData, xmlHeaders, index) == False:
                    print "Failed to get device/service info for %s..." % hostInfo['name']
                    return
                print 'Host data enumeration complete for %s.' % hostInfo['name']
                #self.hp.showCompleteHostInfo(index, False)

    def showDeviceInfo(self, index):
        self.hp.showCompleteHostInfo(index, False)

    def delPortMapping(self, index, proto, wanPort):
        bothTCPandUDP = False

        print "Deleting mapping for WAN port " + str(wanPort) + ", protocol " + str(proto)

        if proto == 'BOTH':
            bothTCPandUDP = True
            proto = 'TCP'

        args = {'NewExternalPort': wanPort,
                'NewProtocol': proto,
                'NewRemoteHost': ''}
        resp = self.sendReq(index, 'WANConnectionDevice', 'WANIPConnection', 'DeletePortMapping', args)
        if self.printPortMappingResponse:
            print resp

        if bothTCPandUDP:
            args['NewProtocol'] = 'UDP'
            resp = self.sendReq(index, 'WANConnectionDevice', 'WANIPConnection', 'DeletePortMapping', args)
            if self.printPortMappingResponse:
                print resp

    def addPortMapping(self, index, proto, wanPort, lanPort, host, description):
        bothTCPandUDP = False
        self.delPortMapping(index, proto, wanPort)

        print "Adding mapping for WAN port " + str(wanPort) + " -> LAN port " + str(lanPort) + ", protocol " + str(proto)

        if proto == 'BOTH':
            bothTCPandUDP = True
            proto = 'TCP'

        args = {
            'NewRemoteHost': '',
            'NewExternalPort': wanPort,
            'NewProtocol': proto,
            'NewInternalPort': lanPort,
            'NewInternalClient': host,
            'NewEnabled': '1',
            'NewPortMappingDescription': description,
            'NewLeaseDuration': '0',
        }

        resp = self.sendReq(index, 'WANConnectionDevice', 'WANIPConnection', 'AddPortMapping', args)
        if self.printPortMappingResponse:
            print resp

        if bothTCPandUDP:
            args['NewProtocol'] = 'UDP'
            resp = self.sendReq(index, 'WANConnectionDevice', 'WANIPConnection', 'AddPortMapping', args)

            if self.printPortMappingResponse:
                print resp

    def showPortMapping(self, index, proto, wanPort):
        bothTCPandUDP = False

        if proto == 'BOTH':
            bothTCPandUDP = True
            proto = 'TCP'

        args = {
            'NewRemoteHost': '',
            'NewExternalPort': wanPort,
            'NewProtocol': proto,
        }

        resp = self.sendReq(index, 'WANConnectionDevice', 'WANIPConnection', 'GetSpecificPortMappingEntry', args)
        print resp

        if bothTCPandUDP:
            args['NewProtocol'] = 'UDP'
            resp = self.sendReq(index, 'WANConnectionDevice', 'WANIPConnection', 'GetSpecificPortMappingEntry', args)
            print resp

    def sendReq(self,index,deviceName,serviceName,actionName,sendArgs):
        try:
            hostInfo = self.hp.ENUM_HOSTS[index]
        except:
            print "Index error"
            return

        newSendArgs = {}
        retTags = []
        response = {}
        controlURL = False
        fullServiceName = False
        actionArgs = False
        inValueMissing = False

        if (sendArgs == None) or len(sendArgs) == 0:
            sendArgs = {}

        #print sendArgs

        # Get the service control URL and full service name
        try:
            controlURL = hostInfo['proto'] + hostInfo['name']
            controlURL2 = hostInfo['deviceList'][deviceName]['services'][serviceName]['controlURL']
            if not controlURL.endswith('/') and not controlURL2.startswith('/'):
                controlURL += '/'
            controlURL += controlURL2
        except Exception, e:
            print 'Caught exception:', e
            print "Are you sure you've run 'host get %d' and specified the correct service name?" % index
            return None

        # Get action info
        try:
            actionArgs = hostInfo['deviceList'][deviceName]['services'][serviceName]['actions'][actionName]['arguments']
            fullServiceName = hostInfo['deviceList'][deviceName]['services'][serviceName]['fullName']
        except Exception, e:
            print 'Caught exception:', e
            print "Are you sure you've specified the correct action?"
            return None

        for argName, argVals in actionArgs.iteritems():
            actionStateVar = argVals['relatedStateVariable']
            stateVar = hostInfo['deviceList'][deviceName]['services'][serviceName]['serviceStateVariables'][
                actionStateVar]

            if argVals['direction'].lower() == 'in':
                if argName in sendArgs:
                    newSendArgs[argName] = (sendArgs[argName], stateVar['dataType'])
                else:
                    inValueMissing = True
                    newSendArgs[argName] = ('', stateVar['dataType'])
                    print "Required argument:"
                    print "\tArgument Name: ", argName
                    print "\tData Type:     ", stateVar['dataType']
                    if stateVar.has_key('allowedValueList'):
                        print "\tAllowed Values:", stateVar['allowedValueList']
                    if stateVar.has_key('allowedValueRange'):
                        print "\tValue Min:     ", stateVar['allowedValueRange'][0]
                        print "\tValue Max:     ", stateVar['allowedValueRange'][1]
                    if stateVar.has_key('defaultValue'):
                        print "\tDefault Value: ", stateVar['defaultValue']
            else:
                retTags.append((argName, stateVar['dataType']))

        #if inValueMissing:
        #    return None

        # print 'Requesting',controlURL
        soapResponse = self.hp.sendSOAP(hostInfo['name'], fullServiceName, controlURL, actionName, newSendArgs)
        if soapResponse != False:
            # It's easier to just parse this ourselves...
            for (tag, dataType) in retTags:
                tagValue = self.hp.extractSingleTag(soapResponse, tag)
                if dataType == 'bin.base64' and tagValue != None:
                    tagValue = base64.decodestring(tagValue)
                #print tag, ':', tagValue
                response[tag] = tagValue
            return response
        return None

    def startThreads(self):
        self.run = True
        self.hp = miranda.upnp(False, False, None, None)
        self.hp.TIMEOUT = 1
        print 'Starting read thread'
        self.readThread = threading.Thread(target=self.readSock, args=())
        self.readThread.start()
        self.THREADS.append(self.readThread)
        print 'Starting search thread'
        self.searchThread = threading.Thread(target=self.msearch, args=("service", "WANIPConnection",))
        self.searchThread.start()
        self.THREADS.append(self.searchThread)

    def stopThreads(self):
        print 'Stopping threads'
        self.run = False
        if self.hp != None:
            try:
                #self.hp.ssock.close()
                self.hp.ssock.shutdown(socket.SHUT_WR)
            except:
                None

    def doPortMapping(self, ip, upnpPortMappings, upnpPortRangeMappings, add):
        index = self.routerIndex

        if index >= 0:
            for entry in upnpPortMappings:
                if add:
                    self.addPortMapping(index, entry[0], entry[1], entry[1], ip, entry[2])
                else:
                    self.delPortMapping(index, entry[0], entry[1])

            for entry in upnpPortRangeMappings:
                start = entry[1]
                end = entry[2]
                while start <= end:
                    if add:
                        self.addPortMapping(index, entry[0], start, start, ip, entry[3])
                    else:
                        self.delPortMapping(index, entry[0], start)
                    start = start + 1

    def showPortMappings(self, upnpPortMappings, upnpPortRangeMappings):
        index = self.routerIndex

        if index >= 0:
            for entry in upnpPortMappings:
                self.showPortMapping(index, entry[0], entry[1])

            for entry in upnpPortRangeMappings:
                start = entry[1]
                end = entry[2]
                while start <= end:
                    self.showPortMapping(index, entry[0], start)
                    start = start + 1
