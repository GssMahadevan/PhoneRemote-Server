from twisted.web.server import Site

#from twisted.web.http import proxiedLogFormatter
from twisted.web.resource import Resource
from twisted.internet import reactor
from twisted.web.static import File
from twisted.web.resource import NoResource
from twisted.internet.task import deferLater
from twisted.web.server import NOT_DONE_YET

from twisted.python.log import err

from calendar import calendar
import time
import cgi
import re
import hashlib
import threading

import irtoy3
import IrToyYs
import serial
import argparse
import os
import binascii
import requests
import traceback

### Not needed for parkin sensor
###from DoorSensors import *

from  MySys import *
#from RPIO_g import sendServoCmd 

debug = False

log = logging.getLogger('twisted-app')

root = Resource()

myprops = {}
mypropsBin = {}
models={}
toy=None

RE_CODE=re.compile('_')
RE_CODE_DOT=re.compile('\.')
useUsbIrToy=False
rawSleep=0.010
httpUrl='http://tvremote.local.net/ir'

class ClockPage(Resource):
    isLeaf = True
    def render_GET(self, request):
        return "<html><body>%s</body></html>" % (time.ctime(),)

class SendRemoteCodePage(Resource):
    def __init__(self, code):
        Resource.__init__(self)
        self.code = code

    def render_GET(self, request):
        request.setHeader("content-type", "application/json")
        return '{"code" : "%s"}' % self.code 

"""
Code for sending USB-IRToy. Not doing any further developement as USB IRtoy is costlier :)
"""
class SendRemoteCode(Resource):
    def getChild(self, name, request):
        code="";
        who=getSessInfo(request)
        try:
            cmds=RE_CODE.split(name)
            loop=0
            for cmd in cmds:
                codes=myprops.get(cmd,None) 
                if codes == None:
                    log.error("SendRemoteCode-1 req failed for "+name+', for cmd:'+cmd+" for "+ who)
                    return NoResource() 
                sendRemoteCode(cmd,codes,who)
                code += codes[0] +";"
                loop += 1
        except ValueError:
            tb=traceback.format_exc()
            log.error("SendRemoteCode-2 req failed for "+name+", loop:"+ loop+" for "+ who+", tb:\n"+tb)
            return NoResource()
        else:
            return SendRemoteCodePage(code)

"""
Code to send IR via ESP8266 module. Format of the HTTP call to ESP8266 is like this:
http://esp-ip/ir?code=comma_seperated_raw_ir_codes_captured_IRremoteESP8266__IRrecvDumpV2_program&hz=correct_hz_based_on_your_receving_device&count=1_or_2

Example call is:

http://192.168.1.2/ir?code=2800,900,500,450,500,450,500,900,550,900,1450,900,500,450,500,450,500,450,500,450,500,450,500,450,500,450,500,450,1000,900,500,450,500,450,1000,450,500,900,500,450,500,450,500,450,500,450,500,450,500,450,500,450,500,450,500,450,500,450,500,450,1000,450,500,900,1000&hz=38&count=1

"""
class SendIRRaw(Resource):
    def getChild(self, name, request):
        who=getSessInfo(request)
        log.debug('SendIRRaw ---> who:'+who+', name:'+name+", ~~~~~~args:" +str(request.args))
        codeA=request.args.get('code',None)
        if len(codeA) == 0:
            return NoResource('No Code specified') 
        code=codeA[0]
        modelA=request.args.get('model',None) 
        if len(modelA) == 0:
            return NoResource('No Model specified') 
        model=modelA[0]
        log.debug('SendIRRaw ---> codes:'+str(code)+', model:'+str(model))
        try:
            loop=0
            modelProp = models.get(model,None)
            if modelProp == None:
                log.error("SendIRRaw-1 req no model for "+name+', for model:'+model+" for "+ who)
                return NoResource() 
       
            freq=modelProp.get('freq','38')
            type=modelProp.get('type','0')
            count=modelProp.get('count',2)
            cmds=RE_CODE_DOT.split(code)
            for cmd in cmds:
                if cmd == 'sleep' :
                    time.sleep(rawSleep)
                    continue

                cmd += '_' + type
                codes=modelProp.get(cmd,None) 
                if codes == None:
                    log.error("SendIRRaw-1 req failed for "+name+', for cmd:'+cmd+" for "+ who)
                    return NoResource() 
                sendRemoteCodebyHttp(cmd,codes,freq,int(count),who)
                loop += 1
        except ValueError:
            tb=traceback.format_exc()
            log.error("SendIRRaw-2 req failed for "+name+", loop:"+ loop+" for "+ who+", tb:\n"+tb)
            return NoResource()
        else:
            return SendRemoteCodePage(code)

def getSessInfo(request):
	ip=request.getClientIP()
	msg='sess: ' + request.getSession().uid+ ', ip:'+ip
	return msg
	

class ShowSession(Resource):
    def render_GET(self, request):
        dumpReq(request)
        ip=request.getClientIP()
        msg='Your session id is: ' + request.getSession().uid+ ', ip:'+ip
        log.info(msg)
        return msg

class ExpireSession(Resource):
    def render_GET(self, request):
        request.getSession().expire()
        
        return 'Your session has been expired.'

def getVal(map,key,defV):
    v=map.get(key)
    if v != None: 
        if type(v) ==  list:
            return v[0]
        else:
            return v
    return defV

def dumpMap(ctx,map):
    print ctx
    msgT=ctx
    for a in map:
        msg = a + '=' + str(map[a])
        print msg
        msgT += '\n'+msg
    log.debug(msgT)

               
def dumpReq(req):
    if debug == False: return
    dumpMap('Arguments are:',req.args)
    dumpMap('Headers are:',req.headers)

def initCfg():   
	pass 

def initWebRes():
    root.putChild("ir", SendIRRaw())
    root.putChild("send", SendRemoteCode())
    root.putChild("clk", ClockPage())
    root.putChild("show", ShowSession())
    root.putChild("expire", ExpireSession())
    factory = Site(root) #,  logPath=b"./tmp/access-logging-demo.log", logFormatter=proxiedLogFormatter)
    return factory

def runServer(factory,port):
    print 'Runing  reactor at:'+str(port)
    log.info( 'Runing  reactor at:'+str(port))
    reactor.listenTCP(port, factory)
    # For errors: exceptions.ValueError: signal only works in main thread 
    # installSignalHandlers=0 to reactor.run(installSignalHandlers) in case , if we run reactor in seperate thread
    reactor.run() # this one will block

def initUsbToy(dev,speed,timeout,useUsbIrToy,args):
	global toy
	log.debug('Trying to open serialDevice '+dev)
	serialDevice = serial.Serial(dev,speed, timeout=timeout)
	log.info('Got serialDevice '+dev)
	if useUsbIrToy:
		log.debug('Trying to init USB IR Toy ')
		toy = irtoy3.IrToy(serialDevice)
	else:
		log.debug('Trying to init  YS-IRTM device')
		toy = IrToyYs.IrToy(serialDevice,speed,args.max,args.sleep)
		
	log.info('Got irtoy '+str(toy))

def runUsbToy():
    log.info('Checking for USB Toy IR Transmitter/Receiver')

SPEEDS="            50 75 110 134 150 200 300 600 1200 1800 2400 4800\n           9600 19200 38400 57600 115200 230400 460800\n"# 500000 576000 921600 1000000 1152000 1500000 2000000 2500000 3000000 3500000 4000000"

def handleArgs():
	parser = argparse.ArgumentParser(description='Smart Phone TV Remote Server')
	parser.add_argument('-D','--debug', help='Debug more messages',  action='store_true',  required=False, default=False)
	parser.add_argument('-S','--standalone', help='Run standalone server',  action='store_true',  required=False, default=False)

	parser.add_argument('-H','--http-url', help='HTTP-URL for IR sending ESP8266',type=str,    required=False, default=httpUrl)
	parser.add_argument('-d','--device', help='USB IR Toy2 serial port ',type=str,    required=False, default='/dev/ttyACM0')
	parser.add_argument('-c','--config', help='File having key codes of Remote ',type=str,    required=False, default='./tv_ir_keycode.txt')
	parser.add_argument('-p','--port', help='HTTP Server port',type=int,    required=False, default=8088)
	parser.add_argument('-b','--speed', help='Serail port speed in bauds'+SPEEDS,type=int,    required=False, default=9600)
	parser.add_argument('-t','--timeout', help='Serail port timeout in seconds',type=int,    required=False, default=1)
	parser.add_argument('-T','--use-usbirtoy', help='Use USB IR Toy for serial communication',action='store_true', required=False, default=False)
	parser.add_argument('-m','--max', help='Max bytes per transaction to YSRTM',type=int, required=False, default=3)
	parser.add_argument('-s','--sleep', help='Sleep in between sends',type=float, required=False, default=0.002)
	parser.add_argument('-e','--esp', help='Use ESP8226 based IR sending rather than USB based IR sending', action='store_true',  required=False, default=True)

	args = parser.parse_args()
	return args

def loadModels():
	global models
	dbg=""
	with open("./model2file.properties", 'r') as f:
		for line in f:
			line = line.rstrip()
			if "=" not in line: continue
			if line.startswith("#"): continue
			k, v = line.split("=", 1)
			dbg += k +'=' +v+ ';;;;;;;;;;;;;;;;;;;;;;;;;;;;\n\n' 
			map={}
			with open(v, 'r') as irF:
				for ir in irF:
					irCode=ir.strip()
					if "=" not in irCode: continue
					if irCode.startswith("#"): continue
					k1, v1 = irCode.split("=", 1)
					map[k1]=v1
					dbg += k1 +'=' +v1+ ';\n' 
			models[k] = map

	log.info('Models are;'+dbg)

def initRemoteCodes(file):
	global myprops
	dbg=""
	with open(file, 'r') as f:
		for line in f:
			line = line.rstrip()
			if "=" not in line: continue
			if line.startswith("#"): continue
			k, v = line.split("=", 1)
			dbg += k +'=' +v+ ';' 
			myprops[k] = [ v, bytearray(binascii.unhexlify(v))] 
	log.info('Key codes are;'+dbg)


def sendRemoteCodebyHttp(name,codes,freq,count,who):
	for i in xrange(count):
		t0=time.time()
		#params={'code':codes,'hz':freq}
		#url=httpUrl+'?code='+str(codes)+'&hz='+str(freq)+"&count="+str(count)
		url=httpUrl+'?code='+str(codes)+'&hz='+str(freq)
		r=requests.get(url)
		t1=time.time()
		log.info("IR code:" + name+', took:'+str((t1-t0))+ ',count:'+str(count)+', freq:'+str(freq)+", r-status"+str(r)+" for "+ who+", code:"+ str(codes)+', sees:'+who)

def sendRemoteCode(name,codes,who):
	global toy
	#log.info("Sending remote code " + name+' , len:'+ str(len(bCode))+', type:'+ str(type(bCode))+ ', code:'+str(bCode))
	##log.info("Trying to Send remote code '" + name+"' , len:"+ str(len(bCode)))
	t0=time.time();
	bCode=codes[1]
	who="USB-IRToy"
	if useUsbIrToy:
		toy.transmit(bCode)
	else:
		who="YS-IRTM"
		toy.sendData(bCode)
	t1=time.time();
	log.info(who+ " After sending remote code '" + name+"' , len:"+ str(len(bCode))+' ,took:'+str((t1-t0))+" for "+ who)

if __name__ == "__main__":
	args=handleArgs()
	standalone=args.standalone
	initLog('./phRemote.log',standalone)
	initCfg()
	rawSleep=args.sleep
	httpUrl=args.http_url
	
	if args.esp :
		loadModels()	
	else:
		useUsbIrToy=args.use_usbirtoy
		initUsbToy(args.device,args.speed,args.timeout,args.use_usbirtoy,args)
		initRemoteCodes(args.config)
	#tUsbIrToy = threading.Thread(name='UsbIrToyThread',target=runUsbToy,)
	#tUsbIrToy.daemon =True
	#tUsbIrToy.start()
	factory=initWebRes()
	runServer(factory,args.port)
