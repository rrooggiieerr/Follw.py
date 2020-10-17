import os, sys, logging, signal, argparse, urllib.parse, platform, multiprocessing

from Follw import Follw
from Location import Location, wifiLocationConfigs, ipLocationConfigs

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def daemonize():
  # Example code from https://gist.github.com/slor/5946334

  # fork 1 to spin off the child that will spawn the daemon
  if os.fork():
    sys.exit()

  # This is the child.
  # 1. cd to root for a guarenteed working dir
  # 2. clear the session id to clear the controlling TTY
  # 3. set the umask so we have access to all files created by the daemon
  os.chdir("/")
  os.setsid()
  os.umask(0)

  # fork 2 ensures we can't get a controlling ttd.
  if os.fork():
    sys.exit()

  # This is a child that can't ever have a controlling TTY.
  # Now we shut down stdin and point stdout/stderr at log files.

  # stdin
  with open('/dev/null', 'r') as dev_null:
    os.dup2(dev_null.fileno(), sys.stdin.fileno())

# Custom argparse validator for URLs
def url(value):
  parsedUrl = urllib.parse.urlparse(value)
  if parsedUrl.scheme and parsedUrl.netloc:
    return value
  
  raise argparse.ArgumentTypeError("%s is an invalid URL" % value)

class IntRange:
  def __init__(self, min=None, max=None):
    self.min = min
    self.max = max

  def __call__(self, arg):
    try:
      value = int(arg)
    except ValueError:
      raise argparse.ArgumentTypeError("Must be an integer")

    if (self.min is not None and value < self.min):
      raise argparse.ArgumentTypeError(f"Must be an integer >= {self.min}")
    if (self.max is not None and value > self.max):
      raise argparse.ArgumentTypeError(f"Must be an integer <= {self.max}")

    return value
  
def main():
  # Read command line arguments
  argparser = argparse.ArgumentParser()
  argparser.add_argument('url', type=url)
  argparser.add_argument("-f", "--foreground", dest="foreground", action="store_const", const=True, default=False, help="Run process in the foreground")
  argparser.add_argument("--oneshot", dest="oneshot", action="store_const", const=True, default=False, help="Submit location only once")
  argparser.add_argument("-i", "--interval", dest="interval", type=IntRange(0), default=Follw.interval, help="Logging interval in seconds (default: %(default)s)")
  argparser.add_argument("--wifi", "--enablewifilocationlookup", dest="wifiLocationLookup", action="store_const", const=True, default=False, help="Enable WiFi location lookup if other methods are unsuccessful")
  argparser.add_argument("--wifilocationprovider", dest="wifiLocationProvider", choices=wifiLocationConfigs.keys(), default=Location.wifiLocationProvider, help="Provider for WiFi location lookup (default: %(default)s)")
  argparser.add_argument("--wigletoken", dest="wigleToken", default=None, help="Your WiGLE authentication token for WiFi location lookup")
  argparser.add_argument("--ip", "--enableiplocationlookup", dest="ipLocationLookup", action="store_const", const=True, default=False, help="Enable IP location lookup if other methods are unsuccessful")
  argparser.add_argument("--iplocationprovider", dest="ipLocationProvider", choices=ipLocationConfigs.keys(), default=Location.ipLocationProvider, help="Provider for IP location lookup (default: %(default)s)")
  args = argparser.parse_args()

  foreground = False
  if args.foreground or args.oneshot:
    foreground = True

  if foreground:
    logging.basicConfig(format='%(levelname)-8s %(message)s')
    stdoutHandler = logging.StreamHandler(sys.stdout)
    stdoutHandler.setLevel(logging.DEBUG)
    stdoutHandler.addFilter(lambda record: record.levelno <= logging.INFO)
    stderrHandler = logging.StreamHandler(sys.stderr)
    stderrHandler.setLevel(logging.WARNING)
    logger.addHandler(stdoutHandler)
    logger.addHandler(stderrHandler)
  #ToDo Where to log to when process is running in the background?
  # A dedicated log file seems a bit overkill
  #else:
  #  logging.basicConfig(filename=logFile, format='%(asctime)s %(levelname)-8s %(name)s.%(funcName)s() %(message)s', datefmt='%x %X', level=logging.INFO)

  follw = Follw()
  signal.signal(signal.SIGINT, follw.stop)
  signal.signal(signal.SIGTERM, follw.stop)

  follw.oneshot = args.oneshot
  follw.interval = args.interval
  follw.location.wifiLocationLookup = args.wifiLocationLookup
  if args.wigleToken:
    follw.location.wifiLocationLookup = True
    follw.location.wifiLocationProvider = 'wigle'
    #ToDo Validate WiGLE token
    follw.location.wigleToken = args.wigleToken
  follw.location.ipLocationLookup = args.ipLocationLookup
  follw.location.ipLocationProvider = args.ipLocationProvider
  # URL is validated by argparse
  follw.url = args.url

  if not follw.oneshot:
    logger.info("Starting follw")

  if foreground:
    try:
      follw.run()
    except (KeyboardInterrupt):
      follw.stop()
  else:
    daemonize()
    follw.run()

if __name__ == '__main__':
  main()