# Follw.app Python client

A Python 3 client for retrieving your device location and sharing it to the Follw.app WebService

## About Follw.app
Follw.app is a privacy focused location sharing service. Only a unique Sharing ID and derived Sharing URL is given and no account details, user credentials, IP addresses, Cookies and other sensitive information are used or stored on the Follw.app servers.

Whenever a new location is submitted the previous location is overwritten, no location history is stored.

Whenever you delete your unique Sharing ID all location details are removed from the Follw.app servers. Only a hash of your Sharing ID is stored after removal to guarantee a Sharing ID is not reassigned again.

## Location retrieval
The Follw.app Python client tries to retrieve your device location depending on the Operating System abilities.

For Linux and other Unices GPSd in combination with a hardware GPS device can be used

For OS X Core Location Service can be used. OS X will ask you to approve Python to use the Core Location Service.

Windows Location Services is not yet implemented due to lack of a Windows development environment. You're invited to implement this functionality.

On Linux en OS X the location of the WiFi Access Point that you use to connect to the internet can be used to retrieved your location. For Windows this should also be possible, however this is not yet implemented due to lack of a Windows development environment.

Independent of the OS the location of the external IP address of your internet connection can be retrieved. This is not very precise at all and in most cases only gives the city where your device is located.

When using WiFi Access Point or external IP address location lookup a third party WebService is used, **Follw.app can not guarantee your privacy when using these external WebServices**. That's why WiFi Access Point and external IP address location lookups are disabled by default and you need to use a command argument to enable one or both options.

When one of the mentioned location retrieval methods can not be found on your device Operating System the Follw.app Python client will fall back to a less precise location retrieval method.

The order of location retrieval methods is as follows:
* GPSd and hardware GPS device
* OS X Core Location Service (or Windows Location Services once implemented)
* WiFi Access Point location lookup, when enabled
* External IP address location lookup, when enabled

## Usage

The Follw.app Python client is written in Python 3, you need a Python 3 interpreter to run this software. How to install Python 3 on your specific Operating System is not in the scope of this document.

If you are using GPSd and a hardware GPS device this needs to be properly configured. How to configure GPSd on your specific Operating System is not in the scope of this document.

If you want to use Core Location on OS X the Python Core Location framework wrapper need to be installed. How to do this is not in the scope of this document.

The Follw.app Python client will by default run in the background as a daemon on Unix like operating systems. This can be overruled by using the `-f` or `--foreground` argument.

```
usage: Follw [-h] [-f] [--oneshot] [-i INTERVAL] [--wifi] [--wifilocationprovider {yandex,wigle}] [--wigletoken WIGLETOKEN] [--ip]
             [--iplocationprovider {ip-api.com,ipapi.co,extreme-ip-lookup.com,ipwhois.io}]
             url

positional arguments:
  url                   your unique Follw.app sharing URL

optional arguments:
  -h, --help            show this help message and exit
  -f, --foreground      run process in the foreground
  --oneshot             submit location only once and exit
  -i INTERVAL, --interval INTERVAL
                        logging interval in seconds (default: 5)
  --wifi, --enablewifilocationlookup
                        enable WiFi location lookup
  --wifilocationprovider {yandex,wigle}
                        provider for WiFi location lookup (default: yandex)
  --wigletoken WIGLETOKEN
                        your WiGLE authentication token for WiFi location lookup
  --ip, --enableiplocationlookup
                        enable external IP address location lookup
  --iplocationprovider {ip-api.com,ipapi.co,extreme-ip-lookup.com,ipwhois.io}
                        provider for external IP address location lookup (default: ip-api.com)
```