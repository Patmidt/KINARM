# -*- coding: utf-8 -*-
"""
Created on Wed Sep 20 12:01:32 2023

@author: Tiziano Weilenmann
"""

import serial
from enum import Enum

# initialize stimulator
"""Connection handler for serial device (stimulator)"""

class Serial_Connection1:
    
    def _init_(self, COMPORT, msgLen):
        self.MESSAGE_LENGTH = msgLen
        self.serialPort = COMPORT
        self.serialDevice = serial.Serial(port=self.serialPort, baudrate=115200, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
    
    #TODO start async task doing reads and using self.callback funtion    
    
    def send(self, data):
        self.serialDevice.write(data)
        pass
    
    
    def read(self):
        #try:
        if self.serialDevice.in_waiting >= self.MESSAGE_LENGTH:
            msg = b""
            for i in range(self.MESSAGE_LENGTH):
                recByte = self.serialDevice.read()

                # Print the contents of the serial data
                try:
                    #print(recByte)
                    msg = msg +recByte
                    #msgDict = {"msg":msg}
                    #♣self.callback(msgDict)
                except:
                    pass
            return msg
        #except:
        #print("read error")
        return -1
        pass
    
    def close(self):
        self.serialDevice.close()

      
    def _init_(self, COMPORT, msgLen):
        self.MESSAGE_LENGTH = msgLen
        self.serialPort = COMPORT
        self.serialDevice = serial.Serial(port=self.serialPort, baudrate=115200, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
    
    #TODO start async task doing reads and using self.callback funtion    
    
    def send(self, data):
        self.serialDevice.write(data)
        pass
    
    
    def read(self):
        #try:
        if self.serialDevice.in_waiting >= self.MESSAGE_LENGTH:
            msg = b""
            for i in range(self.MESSAGE_LENGTH):
                recByte = self.serialDevice.read()

                # Print the contents of the serial data
                try:
                    #print(recByte)
                    msg = msg +recByte
                    #msgDict = {"msg":msg}
                    #♣self.callback(msgDict)
                except:
                    pass
            return msg
        #except:
        #print("read error")
        return -1
        pass
    
    def close(self):
        self.serialDevice.close()
    
class Serial_Connection2:
      
    def _init_(self, COMPORT, msgLen):
        self.MESSAGE_LENGTH = msgLen
        self.serialPort = COMPORT
        self.serialDevice = serial.Serial(port=self.serialPort, baudrate=115200, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
    
    #TODO start async task doing reads and using self.callback funtion    
    
    def send(self, data):
        self.serialDevice.write(data)
        pass
    
    
    
    def read(self):
        #try:
        if self.serialDevice.in_waiting >= self.MESSAGE_LENGTH:
            msg = b""
            for i in range(self.MESSAGE_LENGTH):
                recByte = self.serialDevice.read()

                # Print the contents of the serial data
                try:
                    #print(recByte)
                    msg = msg +recByte
                    #msgDict = {"msg":msg}
                    #♣self.callback(msgDict)
                except:
                    pass
            return msg
        #except:
        #print("read error")
        return -1
        pass
    
    def close(self):
        self.serialDevice.close()
        

"""Enums for identifying messages"""

from enum import Enum
class MSGTYPES(Enum):
    #OSTATE CHANGES
    MSG_STIM_SLEEP = 0
    MSG_STIM_READY = 1
    MSG_STIM_APPLY = 2
    MSG_STIM_STOP = 3
      
    #PULSE DEFINITION
    MSG_BURSTINTERVAL = 10      #"""200- 30000 ms"""#TODO not implemented
    MSG_NUMBURSTS = 11          #"""1- 200"""#TODO not implemented
    MSG_REPORTINTERVAL = 12     #"""100- 10000ms""" #report every nth ms
    MSG_PULSEWIDTH = 13         #"""200- 30000 ms"""
    MSG_FORWARDAMPLITUDE = 14   #"""100- 3000 uA"""
    MSG_PULSEINTERVAL = 15      #"""10000- 1000000 ms"""
    MSG_STIMULATIONTIME = 16    #"""200- 30000 ms"""
      
    MSG_IMPEDANCEMEASUREMENT = 50 #""" Measurement in 10xOhm""" #Feedback impedance measurement
    MSG_STIM_STATE = 51 #Feedback to which state is active
    MSG_REQUEST_SETTINGS = 52
    MSG_KEEPALIVE = 53 #TODO keep alives
    
    #MESSSAGE HANDLING
    MSG_ERROR = 80
    MSG_ACK = 81 #"""contains message type"""
    
    #SPECIAL
    MSG_MULTI = 90
    MSG_UNKNOWN = 91
    pass

class STIMULATION_STATE(Enum):
    SLEEP_STATE = 0
    PREPARE_READY_STATE = 1
    PREPARE_APPLY_STATE = 2
    READY_STATE = 3
    APPLY_STATE = 4
    pass

class STIMULATION_ERRORS(Enum):
  STIM_SUCCESS = 0
  STIM_INVALID_SETTING =1
  STIM_INVALID_MESSAGE =2
  STIM_UNKNOWN_MESSAGE =3
  STIM_NOT_IMPLEMENTED =4
  STIM_ELECTRODE_OFF =5
  STIM_UNKNOWN_ERROR =6
  STIM_TIMEOUT =7
  pass


"""Message factory to create and interpret messages"""

class Message_Factory:
    MESSAGE_LENGTH = 6
    
    def calculate_crc(self, msg: bytes) -> int:
        crc = 0xff
        for b in msg:
            crc ^= b
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x31) & 0xff
                else:
                    crc <<= 1
        return crc
              
    def decrypt_message(self, msg):
        msgDict = {};
        try:
            msgDict["msgType"] = MSGTYPES(int.from_bytes(msg[0:1], "big"))
        except:
            msgDict["msgType"] = MSGTYPES.MSG_UNKNOWN
        
        msgDict["msgValue"] = int.from_bytes(msg[1:5], "big")
        
        if(self.calculate_crc(msg) != 0):
            msgDict["msgType"] = MSGTYPES.MSG_ERROR
            msgDict["error"] = "invalid crc"
        return msgDict
        pass
    
    def encrypt_message(self, msg_type: MSGTYPES, value: int) -> bytes:
        msg = bytearray(self.MESSAGE_LENGTH)
        msg[0] = msg_type.value
        for i in range(1, self.MESSAGE_LENGTH-1):
            msg[i] = (value >> (32-8*i)) & 0xff
        
        crc = self.calculate_crc(msg[:-1])
        msg[self.MESSAGE_LENGTH-1] = crc
        
        return  bytes(msg)
        pass