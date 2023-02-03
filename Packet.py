#packet structure: seq num (4 bytes), ack num (4 bytes), ACK FLAG (1 byte), data
SEP = "------------------------\n"
import hashlib

class Packet:
    def __init__(self,SEQ_NUM=0,ACK_NUM=0,ACK=0,FIN=0,DATA=b" "):
        self.SEQ_NUM = SEQ_NUM
        self.ACK_NUM = ACK_NUM
        self.ACK = ACK
        self.FIN = FIN
        self.DATA = DATA
        self.checksum = None
        self.corrupted = False

    def compute_checksum(self,packet):
        #16 bytes
        checksum = hashlib.md5(packet).digest()
        self.checksum = checksum
        return checksum

    def pack(self):
        print(SEP)
        print("sending a packet, SEQ NUM:",self.SEQ_NUM,"ACK NUM:",self.ACK_NUM,\
              "ACK FLAG:",self.ACK,"FIN FLAG:",self.FIN,"DATA:",self.DATA)
        print(SEP)

        num_part = self.SEQ_NUM.to_bytes(4,"big")+self.ACK_NUM.to_bytes(4,"big")
        # print("num part:",num_part)
        # print("pack printing ACK byte,",self.ACK.to_bytes(1,"little"))
        packet = num_part + self.ACK.to_bytes(1,"little") + self.FIN.to_bytes(1,"little") + self.DATA
        # we will also compute checksum, 16 bytes
        self.compute_checksum(packet)
        return self.checksum + packet


    def unpack(self,segment):
            #take a segment and parse its attribute
        # print("unpacking",segment)
        old_checksum = segment[:16]
        header_part = segment[16:26]
        self.ACK = header_part[8]
        self.FIN = header_part[9]
        self.DATA = segment[26:]
        self.SEQ_NUM = int.from_bytes(header_part[:4],"big")
        self.ACK_NUM = int.from_bytes(header_part[4:8],"big")

        print(SEP)
        print("received a packet, SEQ NUM:",self.SEQ_NUM,"ACK NUM:",self.ACK_NUM,"ACK FLAG:",self.ACK,"FIN FLAG",\
              self.FIN,"DATA:",self.DATA)
        print(SEP)

        #compute new checksum
        recv_packet = segment[16:]
        new_checksum = self.compute_checksum(recv_packet)
        if new_checksum != old_checksum:
            self.corrupted = True