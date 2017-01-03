# xerxesUPnP: Python Port Forwarding Script
Based on miranda-upnp: https://github.com/0x90/miranda-upnp 
## xerxesUPnP is an easy-to-use python library for managing UPnP port forwarding.  The library will automatically detect your WANIPConnection device, then allow you to add/remove port forwarding rules.
## Testing
To test your UPnP device, clone this repository with:

`git clone https://github.com/Xerxes3rd/xerxesUPnP.git`

Then run the test app and save the output:

`./xerxesUPnP/upnp_test.py > test.txt`

Copy the test output to sprunge:

`cat test.txt | curl -F 'sprunge=<-' http://sprunge.us`

Then, send the resulting link to someone (probably me) for analysis.
