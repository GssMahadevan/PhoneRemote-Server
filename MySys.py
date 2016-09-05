import glob
import logging
import logging.handlers
from twisted.internet import reactor

import signal
import sys
reactor_active=False

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    #if reactor_active:
    reactor.stop()
    logging.shutdown()
    sys.exit(0)

def initLog(fileName,standalone):
#    import logging.config
    if fileName == None: fileName = './app.log'
    #if standalone: 
    signal.signal(signal.SIGINT, signal_handler)
    logging.basicConfig(level=logging.DEBUG, filename=fileName,format='%(asctime)s %(levelname)s [%(threadName)s] %(message)s')

isactive=True
class MySys:
    logfile = './mylog.log'

    @staticmethod
    def isActive():
        return isactive

    @staticmethod
    def setActive(v):
        isactive=v

    @staticmethod
    def setReactor():
        reactor_active=True


