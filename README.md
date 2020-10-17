# Follw.app Python client

A Python client for retrieving your device location and sharing it to the Follw.app WebService

## About Follw.app
Follw.app is a privacy focused location sharing service. Only a unique Sharing ID and derived Sharing URL is given and no account details, user credentials, IP addresses, Cookies and other sensitive information are are used or stored on the Follw.app servers.

Whenever a new location is submitted the previous location is overwritten, no location history is stored.

Whenever you delete your unique Sharing ID all location details are removed from the Follw.app servers. Only a hash of your Sharing ID is stored after removal to guarantee a Sharing ID is not reassigned again.

## Location retrieval
The Follw.app Python client tries to retrieve your device location depending on the Operating Sytem abilities.

For Linux and onder Unices GPSd and a hardware GPS device can be used

For OS X Core Location Service is used. OS X will ask you to approve Python to use the Core Location Service.

Windows Location Services is not yet implemented due to lack of a Windows development environment. You're invited to implement this functionality.

On Linux en OS X the location of the WiFi Access Point that you use to connect to the internet can be used to retrieved your location. For Windows this should also be possible, however thi is not yet implemented due to lack of a Windows development environment.

Independent of the OS the location of the external IP address of your internet connection can be retrieved. This is not very precise at all and in most cases only gives the city your device located.

When using WiFi AP or IP location lookup an external WebService is used, **Follw.app can not guarantee your privacy when using these external WebServices**. That's why WiFi AP and IP location lookup are disabled by default and you need to use an command argument to enable one or both options.