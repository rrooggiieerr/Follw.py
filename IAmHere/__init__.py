import sys, logging, signal, time, urllib.request, json, os, platform, subprocess, re

ipLocationConfigs = {
  'ip-api.com': { 'url': 'http://ip-api.com/json/?fields=49344', 'latitudeKey': 'lat', 'longitudeKey': 'lon', 'interval': 60/45},
  'ipapi.co': { 'url': 'https://ipapi.co/json/', 'latitudeKey': 'latitude', 'longitudeKey': 'longitude', 'interval': (60*60*24)/1000},
  'extreme-ip-lookup.com': { 'url': 'https://extreme-ip-lookup.com/json/', 'latitudeKey': 'lat', 'longitudeKey': 'lon', 'interval': (60*60*24*31)/10000},
  'ipwhois.app': { 'url': 'https://ipwhois.app/json/?objects=latitude,longitude', 'latitudeKey': 'latitude', 'longitudeKey': 'longitude', 'interval': (60*60*24*31)/10000}
}

terminate = False
url = None
interval = 5

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

gpsd = None
try:
  from gps import *
except ImportError:
  logger.warning("Python GPSd library not installed")

coreLocation = False
if platform.system() == 'Darwin':
  try:
    import CoreLocation
    coreLocation = True
  except ImportError:
    logger.warning("CoreLocation library not installed")
    coreLocation = False
coreLocationManager = None

locationService = False
if platform.system() == 'Windows':
  locationService = True

wifiLocationLookup = True
previousBSSID = None

ipLocationLookup = True
ipLocationProvider = 'ip-api.com'
ipLocationConfig = None

def stop(signum = None, frame = None):
  """ Stop the IAmHere process """
  global terminate

  logger.info("Stopping IAmHere process ")
  terminate = True

def run():
  """ The main loop of the IAmHere process """
  global terminate
  global gpsd
  global url
  global interval
  global wifiLocationLookup
  global ipLocationConfigs, ipLocationConfig, ipLocationProvider, ipLocationLookup

  if 'gps' in sys.modules:
    try:
      gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
    except ConnectionRefusedError as e:
      logger.warning("Can't connect to GPSd")

  ipLocationConfig = ipLocationConfigs[ipLocationProvider]

  previousLocation = None
  _time = 0
  while not terminate:
    location = None

    elapsedTime = time.time() - _time
    #logger.debug(elapsedTime)
    if elapsedTime > interval:
      if gpsd:
        location = getGPSLocation()
        if location:
          logger.debug(location)
          _time = time.time()

      if not location and coreLocation:
        location = getCoreLocationLocation()
        if location:
          logger.debug(location)
          _time = time.time()

      if not location and locationService:
        location = getLocationServiceLocation()
        if location:
          logger.debug(location)
          _time = time.time()

      if not location and wifiLocationLookup:
        location = getWiFiLocation()
        if location:
          logger.debug(location)
          _time = time.time()

    if not location and ipLocationLookup and elapsedTime > interval and elapsedTime > ipLocationConfig['interval']:
      location = getIPLocation()
      if location:
        logger.debug(location)
        _time = time.time()

    if location and location != previousLocation:
      try:
        _url = '{}?la={}&lo={}'.format(url, location[0], location[1])
        if len(location) >2:
          _url += '&ac={}'.format(location[2])
        if len(location) > 3:
          _url += '&al={}'.format(location[3])
        logger.debug(_url)
        urllib.request.urlopen(_url, timeout=1)
        previousLocation = location
      except urllib.error.URLError as e:
        logger.error(e.reason)
      except urllib.error.HTTPError as e:
        logger.error(e.code)

    time.sleep(0.1)

  logger.info("Stopped IAmHere daemon")

def getGPSLocation():
  """ Get the location using the GPS daemon """
  global gpsd

  if gpsd:
    _time = time.time()
    while not terminate:
      if gpsd.waiting():
        # Get current location from GPS device
        report = gpsd.next()
        if report['class'] == 'TPV':
          if report['mode'] in [0, 1]:
            return None

          if 'lat' in report and 'lon' in report:
            return [ report['lat'], report['lon'] ]

          logger.debug(report)
          return None
        elif report['class'] == 'DEVICES':
          if len(report['devices']) == 0:
            logger.warning("No GPS device connected")
            return None
          _time = time.time()
        elif report['class'] == 'SKY':
          if 'satellites' not in report:
            logger.debug("No satellites in view")
            return None
          _time = time.time()
        else:
          logger.debug(report)
          _time = time.time()
      else:
        elapsedTime = time.time() - _time
        logger.debug(elapsedTime)
        if elapsedTime > 1:
          return None
        time.sleep(0.1)

  return None

def getCoreLocationLocation():
  """ Get the location using the macOS Core Location API """
  global coreLocation, coreLocationManager

  if platform.system() == 'Darwin' and coreLocation:
    if not coreLocationManager:
      coreLocationManager = CoreLocation.CLLocationManager.alloc().init()
      coreLocationManager.delegate()
      coreLocationManager.startUpdatingLocation()
    logger.debug(coreLocationManager.location())

    location = coreLocationManager.location()
    if location:
      coord = location.coordinate()
      logger.debug(location.horizontalAccuracy())
      return [coord.latitude, coord.longitude, location.horizontalAccuracy()]
    
    logger.debug("Core Location could not find your location")
    return None

  logger.debug("Core Location not supported")
  return None

def getLocationServiceLocation():
  """ Get the location using the Windows Location Service API """
  if platform.system() == 'Windows':
    #ToDo
    logger.debug("Location Service not yet implemented")
    return None

  logger.debug("Location Service not supported")
  return None

def getWiFiLocation():
  """ Get the location using the WiFi BSSID """
  global previousBSSID

  bssid = None
  
  if platform.system() == 'Linux':
    # Get the default route interface
    proc = subprocess.Popen(['ip', 'route', 'show', 'default'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    proc.wait()
    output = proc.stdout.read().decode()

    interfaces = re.findall("^default via [0-9.]* dev ([^ ]*)", output, re.MULTILINE)
    interfaces = list(set(interfaces))

    if len(interfaces) != 1:
      logger.warning("More than one default route interfaces detected")
      return None

    interface = interfaces[0]
    proc = subprocess.Popen(['iwconfig', interface], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    proc.wait()
    output = proc.stdout.read().decode()
    bssids = re.findall("Access Point: ([0-9a-fA-F:]*)", output, re.MULTILINE)
    signals = re.findall("Signal level=(-[0-9]*) dBm", output, re.MULTILINE)

    if len(bssids) == 0:
      logger.warning("No AP BSSID detected")
      return None
    if len(bssids) > 1:
      logger.warning("More than one AP BSSID detected")

    if len(signals) == 0:
      logger.warning("No AP BSSID detected")
      return None
    if len(signals) > 1:
      logger.warning("More than one AP BSSID detected")

    bssid = bssids[0]
    signal = signals[0]
  elif platform.system() == 'Darwin':
    proc = subprocess.Popen(['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/A/Resources/airport', '-I'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    proc.wait()
    output = proc.stdout.read().decode()
    bssids = re.findall("^ *BSSID: ([0-9a-fA-F:]*)", output, re.MULTILINE)
    signals = re.findall("^ *agrCtlRSSI: (-[0-9]*)", output, re.MULTILINE)

    if len(bssids) == 0:
      logger.warning("No AP BSSID detected")
      return None
    if len(bssids) > 1:
      logger.warning("More than one AP BSSID detected")

    if len(signals) == 0:
      logger.warning("No AP BSSID detected")
      return None
    if len(signals) > 1:
      logger.warning("More than one AP BSSID detected")

    bssid = bssids[0]
    signal = signals[0]
  elif platform.system() == 'Windows':
    #ToDo
    logger.info("WiFi AP location lookup not yet implemented on Windows")
    return None

  if bssid and bssid != previousBSSID:
    _bssid = bssid.replace(':', '')
    url = "http://mobile.maps.yandex.net/cellid_location/?wifinetworks={}:{}".format(_bssid, signal)
    logger.debug(url)
    try:
      with urllib.request.urlopen(url, timeout=1) as response:
        data = response.read().decode('utf-8')
        logger.debug(data)
        latitude = float(re.compile(" latitude=\"([0-9.]*)\".*", re.MULTILINE).search(response).group(1))
        longitude = float(re.compile(" longitude=\"([0-9.]*)\".*", re.MULTILINE).search(response).group(1))
        return [latitude, longitude]
    except urllib.error.HTTPError as e:
      if e.code == 404:
        logger.debug("No location found for BSSID {}".format(bssid))
      else:
        logger.error(e.code)
    except urllib.error.URLError as e:
      logger.error(e)
    previousBSSID = bssid

  return None

def getIPLocation():
  """ Get the location using the external IP address """
  global ipLocationConfig

  try:
    with urllib.request.urlopen(ipLocationConfig['url'], timeout=1) as response:
      data = response.read().decode('utf-8')
      data = json.loads(data)
      return [ data.get(ipLocationConfig['latitudeKey']), data.get(ipLocationConfig['longitudeKey']) ]
  except urllib.error.URLError as e:
    logger.error(e.reason)
  except urllib.error.HTTPError as e:
    logger.error(e.code)

  return None
