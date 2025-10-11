import pprint as pp
import simplepyble
import time
class Packet:
    def __init__(self, ver, seq, timestamp, flags, heartrate, spo2, skinTemp, rms):
        self.ver = ver
        self.seq = seq
        self.timestamp = timestamp
        self.flags = flags
        self.heartrate = heartrate
        self.spo2 = spo2
        self.skinTemp = skinTemp
        self.rms = rms
        self.checkSum = (ver + seq + timestamp + flags + heartrate + spo2 + skinTemp + rms) % 256
        self.full = (self.checkSum<<(14*8)) | (rms<<(12*8)) | (skinTemp<<(10*8)) | (spo2<<(9*8)) | (heartrate<<(8*8)) | (flags<<(7*8)) | (timestamp<<(3*8)) | (seq<<(1*8)) | ver
       
class Wristband:
    '''
    Class for wristbands, containing its name, id, and info packet.
    '''
    wristId = 0
    def __init__(self, name):
        self.name = name
        self.packet = Packet(0x01, 0x003C, 0x0001D4C0, 0x02, 0x4C, 0x62, 0x0E42, 0x00B4)
        

w1 = Wristband('Wristband1')
print(hex(w1.packet.full))
