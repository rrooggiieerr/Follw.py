import os, sys, logging, signal, argparse
import __init__ as IAmHere

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

  # stderr - do this before stdout so that errors about setting stdout write to the log file.
  #
  # Exceptions raised after this point will be written to the log file.
  sys.stderr.flush()
  with open(stderr, 'a+') as stderr:
    os.dup2(stderr.fileno(), sys.stderr.fileno())

  # stdout
  #
  # Print statements after this step will not work. Use sys.stdout
  # instead.
  sys.stdout.flush()
  with open(stdout, 'a+') as stdout:
    os.dup2(stdout.fileno(), sys.stdout.fileno())

if __name__ == '__main__':
  # Read command line arguments
  argparser = argparse.ArgumentParser()
  argparser.add_argument('url')
  argparser.add_argument("-f", "--foreground", dest="foreground", action="store_const", const=True, default=False, help="Run process in the foreground")
  argparser.add_argument("-i", "--interval", dest="interval", type=int, default=IAmHere.interval, help="Logging interval in seconds (default: %(default)s)")
  argparser.add_argument("--nowifi", "--nowifilocationlookup", dest="wifiLocationLookup", action="store_const", const=False, default=True, help="Don't fall back to WiFi AP location lookup if other methods are unsuccessful")
  argparser.add_argument("--noip", "--noiplocationlookup", dest="ipLocationLookup", action="store_const", const=False, default=True, help="Don't fall back to IP location lookup if other methods are unsuccessful")
  argparser.add_argument("--iplocationprovider", dest="ipLocationProvider", choices=IAmHere.ipLocationConfigs.keys(), default=IAmHere.ipLocationProvider, help="Provider for IP location lookup (default: %(default)s)")
  args = argparser.parse_args()

  if args.foreground:
    logging.basicConfig(format='%(levelname)-8s %(message)s')
  #else:
  #  logging.basicConfig(filename=logFile, format='%(asctime)s %(levelname)-8s %(name)s.%(funcName)s() %(message)s', datefmt='%x %X', level=logging.INFO)

  logger.info("Starting IAmHere")

  signal.signal(signal.SIGINT, IAmHere.stop)
  signal.signal(signal.SIGTERM, IAmHere.stop)

  IAmHere.url = args.url
  if args.interval:
    IAmHere.interval = args.interval
  IAmHere.wifiLocationLookup = args.wifiLocationLookup
  IAmHere.ipLocationLookup = args.ipLocationLookup
  if args.ipLocationProvider:
    IAmHere.ipLocationProvider = args.ipLocationProvider

  if args.foreground:
    try:
      IAmHere.run()
    except (KeyboardInterrupt):
      IAmHere.stop()
  else:
    daemonize()
    IAmHere.run()
