#!/usr/bin/env python
#
# Class for simplifying the reading and transmitting of IR signals from the IR Toy.
# This only works for firmware revision 22 or greater.
# see https://github.com/crleblanc/PyIrToy and
# http://dangerousprototypes.com/docs/USB_Infrared_Toy for more info.
#
# Chris LeBlanc, 2012

# GSS Mahadevan 2016
#
# Hacked original code ( by above for ISB-Ir-Toy code) to suite Capturing/Reading
# writing to  Chinese based # YS-IRTM based IR sender/receiver. 
# Not working properly as receiver does not understand IR codes send by the module -- though it sends and receives the IR
#--
#
# This work is free: you can redistribute it and/or modify it under the terms 
# of Creative Commons Attribution ShareAlike license v3.0
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the License for more details. You should have received a copy of the License along 
# with this program. If not, see <http://creativecommons.org/licenses/by-sa/3.0/>.

import time
import binascii

#http://forum.arduino.cc/index.php?topic=359707.0
# https://drive.google.com/folderview?id=0B6uNNXJ2z4CxbUxOdk1Ob3MyTXc&usp=sharing

#
thor__ = 'GSS Mahadevan'
__version__ = '0.1'
__email__ = 'sgorti@gmail.com'

class FirmwareVersionError(Exception):
    pass

class IRTransmitError(Exception):
    pass


class IrToy(object):

	def initBaud(self):
		#self.write([0xA1,0xFA])
		self.write([0xA1,0xFA,0xA1,0xF3,0x02,0x00,0x00])
		#self.write([0xA1,0xF2,0XA5,0x00,0x00])
		baud=self.speed
		print 'baud:' , baud
		if baud == 4800:
			self.write([0xA1,0xF3,0x01,0x00,0x00])    
		elif baud == 9600:
			self.write([0xA1,0xF3,0x02,0x00,0x00])    
		elif baud == 18400:
			self.write([0xA1,0xF3,0x03,0x00,0x00])    
		elif baud == 57600:
			self.write([0xA1,0xF3,0x04,0x00,0x00])    
		else:
			self.write([0xA1,0xF3,0x02,0x00,0x00])


	def __init__(self, serialDevice,baud=9600,max=3,sleeptime=0.002):
		'''Create a new IrToy instance using the serial device for the USB IR Toy'''
		self.toy = serialDevice
		
		self.sleepTime = sleeptime
		self.handshake = None
		self.byteCount = None
		self.complete = None
		self.max=max
		self.speed=baud
		self.initBaud()

	def write(self,code):
		byteCode = bytearray(code)
		bytesWritten = 0
		
		# 31 * 2 bytes = max of 62 bytes in the buffer.  31 hangs so using 32, strange.
		maxWriteSize = 32
		for idx in range(0, len(code), maxWriteSize):
			segmentWritten = self.toy.write(byteCode[idx:idx+maxWriteSize])
			bytesWritten += segmentWritten

	def sendData(self,code):
		dbgC=""
		dbg=""
		len1=len(code)
		print binascii.hexlify(code)
		it = zip(*[iter(code)] * self.max)
		self.initBaud()
		t0=time.time()
		for d in it:
			b=list(d)
			#dbgC += 'type :'+str(type(d)) +  '---> ' + str(d)+" ,   b: " +  str(b) + "b-type:" + str( type(b))
			code=bytearray(b'\xA1\xF1') + bytearray(b) 
			#dbg += binascii.b2a_hex(code) + '\n'
			#self.initBaud()
			self.write(code)
			time.sleep(self.sleepTime)

		t1=time.time()
		#print dbgC
		#print dbg
		print 'Time taken:' + str(t1-t0)	+', len:'+ str(len1)

	def setCustomInit(self,customCode):
		self._writeList(customCode)

	def firmware_revision(self):
		'''Return the hardware and firmware revision returned as a tuple'''
		self.reset()
		#self.toy.write(b'v')
		self._sleep()

		##versionString = self.toy.read(4)
		##hardwareVersion = int(versionString[1:2])
		##firmwareVersion = int(versionString[2:4])

		#return hardwareVersion, firmwareVersion

	def _sleep(self):
		time.sleep(self.sleepTime)

	def _setSamplingMode(self):
		'''set the IR Toy to use sampling mode, which we use exclusively'''
		self.reset()

		#self.toy.write(b'S')

		self._sleep()

		#self.protocolVersion = self.toy.read(3)

		#self._sleep()

	def _writeList(self, code, check_handshake=False):
		'''write a list like object of integer values'''

		self._sleep()

		byteCode = bytearray(code)
		bytesWritten = 0

		# 31 * 2 bytes = max of 62 bytes in the buffer.  31 hangs so using 32, strange.
		maxWriteSize = 32
		for idx in range(0, len(code), maxWriteSize):
			segmentWritten = self.toy.write(byteCode[idx:idx+maxWriteSize])
			bytesWritten += segmentWritten

		#if check_handshake:
		#    self.handshake = ord(self.toy.read(1))

		if bytesWritten != len(code):
			raise IOError("incorrect number of bytes written to serial device, expected %d" % len(code))

	def _getTransmitReport(self):
		'''get the byteCount and completion status from the IR Toy'''

		hexBytes = binascii.b2a_hex(self.toy.read(3)[1:])
		self.byteCount = int(hexBytes, 16)
		#self.complete = self.toy.read(1)

	def _setTransmit(self):

		self._sleep()
		#self._writeList([0x26]) #Enable transmit handshake
		#self._writeList([0x25]) #Enable transmit notify on complete
		#self._writeList([0x24]) #Enable transmit byte count report
		#self._writeList([0x03], check_handshake=True) #Expect to receive packets to transmit
		self.transmitMode = True

	def receive(self,count=256,timeout=5):
		'''Read a signal from the toy, returns a list of IR Codes converted from hex to ints.  See 
	http://dangerousprototypes.com/docs/USB_IR_Toy:_Sampling_mode for more information on the
	sample format.  Reading starts when an IR signal is received and stops after 1.7 seconds of 
	inactivity'''
		self.toy.setTimeout(timeout)
		self.initBaud()
		#self._sleep()
		#self.write([0xA1,0xFA])

		# reset and put back in receive mode in case it was in transmit mode or there was junk in the buffer
		#self._setSamplingMode()

		bytesToRead=count
		readCount=0
		irCode = []

		##while(readCount <  count):
		##	readVal = self.toy.read(1)
		##	if readVal == '' : break # timeout case
		##	#hexVal = binascii.b2a_hex(readVal)
		##	#intVal = int(hexVal, 16)
		##	#print 'hex:', hexVal
		##	irCode.append(readVal)

		##	#if readCount >= 2 and intVal == 255 and irCode[-2] == 255:
		##	#	break

		##	readCount += 1
		return self.toy.read(count)

		#self._sleep()

		##return irCode

	def reset(self):
		'''Reset the IR Toy to sampling mode and clear the Toy's 62 byte buffer'''

		##gssm self._sleep()
		self._writeList([0x00]*5)
		self.transmitMode = False
		self._sleep()

	def transmit(self, code):
		'''switch to transmit mode and write the list (or list-like) set of ints to the toy for transmission,
		Must be an even number of elements.  The list created by read() can be used for transmitting.  If the
		last two elements of the list are not 0xff these will be appended.'''

		if len(code) < 2:
			raise ValueError("Length of code argument must be greater than or equal to two")

		if len(code) % 2 != 0:
			raise ValueError("Length of code argument must be an even number")

		# ensure the last two codes are always 0xff (255) to tell the IR Toy it's the end of the signal
		if code[-2:] != [0xff, 0xff]:
			code.extend([0xff, 0xff])
		nCode = bytearray(b'\xA1\xF1') + code
		code = nCode
		try:
			#self._sleep()
			self._setTransmit()
			self._writeList(code, check_handshake=True)
			self._sleep()
			#self._getTransmitReport()

			#if self.complete not in [b'c', b'C']:
			#    raise IRTransmitError("Failed to transmit IR code, report=%s" % self.complete)
		except:
			# if anything went wrong then sheepishly try to reset state and raise the exception,
			# surprisingly common on a weak CPU like the raspberry pi
			#self.toy.flushOutput() # hmm, maybe this will help? Interesting: we get a crazy state until a new program is started, then fine.
			self.reset()
			self._setSamplingMode()
			raise

		# experimentation shows that returning to sampling mode is needed to avoid dropping the serial connection on Linux
		self._setSamplingMode()
