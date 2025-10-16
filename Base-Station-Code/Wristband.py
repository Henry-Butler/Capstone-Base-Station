import pprint as pp
import simplepyble
import time
# class Packet:
#     def __init__(packet):
#         self.ver = ver
#         self.seq = seq
#         self.timestamp = timestamp
#         self.flags = flags
#         self.heartrate = heartrate
#         self.spo2 = spo2
#         self.skinTemp = skinTemp
#         self.rms = rms
#         self.checkSum = (ver + seq + timestamp + flags + heartrate + spo2 + skinTemp + rms) % 256
#         self.full = (self.checkSum<<(14*8)) | (rms<<(12*8)) | (skinTemp<<(10*8)) | (spo2<<(9*8)) | (heartrate<<(8*8)) | (flags<<(7*8)) | (timestamp<<(3*8)) | (seq<<(1*8)) | ver
#     def __str__(self):
#         return hex(self.full)
class Wristband:
    '''
    Class for wristbands, containing its name, id, and info packet.
    '''
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.packet = 0x0
    def receive_packet(data):
        incomingPacket = data
        if sum(incomingPacket[0:13]) != incomingPacket[14]:
            return
        else:
            packet = data


w1 = Wristband('Wristband1', 0)
print(w1.getPacket())
