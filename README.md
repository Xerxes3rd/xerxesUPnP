# xerxesUPnP: Python Port Forwarding Script
Based on miranda-upnp: https://github.com/0x90/miranda-upnp 
## What does it do?
xerxesUPnP is an easy-to-use python library for managing UPnP port forwarding.  The library will automatically detect your WANIPConnection device, then allow you to add/remove port forwarding rules.
## Testing
To test your UPnP device, clone this repository with:

`cd ~ && git clone https://github.com/Xerxes3rd/xerxesUPnP.git && cd -`

(or, if you've already cloned it, run: `cd ~/xerxesUPnP/ && git pull && cd -` to get the latest version)

Then run the test app and save the output:

`~/xerxesUPnP/upnp_test.py > test.txt`

Copy the test output to sprunge:

`cat test.txt | curl -F 'sprunge=<-' http://sprunge.us`

Then, send the resulting link to someone (probably me) for analysis.
