#packet structure: seq num (4 bytes), ack num (4 bytes), ACK FLAG (1 byte), data

class Packet:
    def __init__(self,SEQ_NUM=0,ACK_NUM=0,ACK=0,FIN=0,DATA=b" "):
        self.SEQ_NUM = SEQ_NUM
        self.ACK_NUM = ACK_NUM
        self.ACK = ACK
        self.FIN = FIN
        self.DATA = DATA

    def pack(self):
        num_part = self.SEQ_NUM.to_bytes(4,"big")+self.ACK_NUM.to_bytes(4,"big")
        # print("num part:",num_part)
        # print("pack printing ACK byte,",self.ACK.to_bytes(1,"little"))
        return num_part + self.ACK.to_bytes(1,"little") + self.FIN.to_bytes(1,"little") + self.DATA


    def unpack(self,segment):
            #take a segment and parse its attribute
        # print("unpacking",segment)
        header_part = segment[0:10]
        self.ACK = header_part[8]
        print("ACK Flag",self.ACK)
        self.FIN = header_part[9]
        print("FIN flag",self.FIN)
        self.DATA = segment[10:]
        print("Data",self.DATA)
        self.SEQ_NUM = int.from_bytes(header_part[:4],"big")
        print("SEQ:",self.SEQ_NUM)
        self.ACK_NUM = int.from_bytes(header_part[4:8],"big")
        print("ACK",self.ACK_NUM)