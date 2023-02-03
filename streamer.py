# do not import anything else from loss_socket besides LossyUDP
import struct
# import time
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
from concurrent.futures import *
import time
from Packet import Packet


# packet structure:
# 1。 data packet: seq number(4 bytes) + data
# 2. ACK packet: ACK + ACK NO

class Streamer:
    def __init__(self, dst_ip, dst_port,
                 src_ip=INADDR_ANY, src_port=0):
        """Default values listen on all network interfaces, chooses a random source port,
           and does not introduce any simulated packet loss."""
        self.socket = LossyUDP()
        self.socket.bind((src_ip, src_port))
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.sender_seq = 0
        self.receiver_seq = 0
        self.buf = {}
        self.acked = {}
        self.closed = False
        self.sleep_interval = 0.01
        # open up worker thread
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.executor.submit(self.recv_listener)
        self.MAX_PACKET_SIZE = 1446

        self.remote_half_closed = False
        self.self_half_closed = False
        self.fin_wait_period = 2.0 # time to wait after receving a FIN from the other side

    def recv_listener(self):

        while not self.closed:
            try:
                # this will be called when there is data to be read
                data, addr = self.socket.recvfrom()
                # check if this packet is data, or ACK?
                # if it's an ACK, set the acked buffer
                # it its data, read the data
                try:
                    segment = Packet()
                    print("received a packet")
                    segment.unpack(data)
                    # is packet corrupted:
                    if segment.corrupted:
                        print("packet corrupted!")
                        continue
                    if segment.ACK == 1:
                        # ack
                        print("ACKing seq", segment.ACK_NUM)
                        # fill buffer
                        self.acked[segment.ACK_NUM] = True
                    if segment.FIN == 1:
                        # fin, send an ack
                        self.receiver_seq += 1 # the length of data packet of a fin is 1
                        fin_ack = Packet(SEQ_NUM=self.sender_seq,\
                                         ACK_NUM=self.receiver_seq,\
                                         ACK=1, FIN=0).pack()
                        self.socket.sendto(fin_ack, (self.dst_ip, self.dst_port))
                        self.remote_half_closed = True
                    else:
                        print("Data segment", segment.SEQ_NUM)
                        self.buf[segment.SEQ_NUM] = segment.DATA
                        # next, the main thread will read this data from buffer

                except Exception as e:
                    print("error decoding")


            except Exception as e:
                print("listner died", e)

    def send(self, data_bytes: bytes) -> None:
        # #     """Note that data_bytes can be larger than one packet."""
        # #     # Your code goes here!  The code below should be changed!
        # #     i = 0
        #     #L = 1468
        while len(data_bytes) > self.MAX_PACKET_SIZE:
            segment = Packet(SEQ_NUM=self.sender_seq, \
                             ACK_NUM=0, ACK=0, \
                             DATA=data_bytes[:self.MAX_PACKET_SIZE]).pack()
            self.socket.sendto(segment, (self.dst_ip, self.dst_port))
            data_bytes = data_bytes[self.MAX_PACKET_SIZE:]
            self.sender_seq += self.MAX_PACKET_SIZE
            self.wait_for_ack(segment)

        if len(data_bytes) == 0:
            return

        segment = Packet(SEQ_NUM=self.sender_seq, ACK_NUM=0, \
                         ACK=0, DATA=data_bytes).pack()
        self.sender_seq += len(data_bytes)
        self.socket.sendto(segment, (self.dst_ip, self.dst_port))
        # we are going to wait for the ACK with ACK NO (self.sender_seq)
        # waiting for an ack with ack=self.sender_seq

        # the timeout for waiting for the ACK is 0.25. If still no ACK, resend
        self.wait_for_ack(segment)
        print("ack received")
        del self.acked[self.sender_seq]

    def wait_for_ack(self, segment):
        # this function use a while loop to wait for the arrival of ack
        start_ack_wait = time.time()
        while self.sender_seq not in self.acked:
            time.sleep(self.sleep_interval)
            ack_wait_elapse = time.time() - start_ack_wait
            if ack_wait_elapse >= 0.25:
                # resend
                self.socket.sendto(segment, (self.dst_ip, self.dst_port))
                # reset timer
                start_ack_wait = time.time()

    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""
        # if the expected seq number is not in receive buffer, sleep
        while self.receiver_seq not in self.buf:
            if len(self.buf) == 0:
                time.sleep(self.sleep_interval)
            elif max(self.buf) < self.receiver_seq:
                ack_segment = Packet(SEQ_NUM=self.sender_seq,ACK_NUM= self.receiver_seq, \
                             ACK=1, FIN=0, DATA=b"").pack()
                self.socket.sendto(ack_segment, (self.dst_ip, self.dst_port))
            else:
                time.sleep(self.sleep_interval)
                
        # read data from buffer

        segment = self.buf[self.receiver_seq]
        decoded_segment = segment.decode("utf-8")
        print("main thread trying to read ", self.receiver_seq, "the data is", decoded_segment, \
              "data length:", len(decoded_segment))

        # clear this data from buffer
        del self.buf[self.receiver_seq]

        # the length should get incremented by the decoded length
        self.receiver_seq += len(segment.decode("utf-8"))
        print("next expected seq:", self.receiver_seq)
        # send an ACK to the sender.  seq num does not change, ack number is the receiver seq
        ack_segment = Packet(SEQ_NUM=self.sender_seq,ACK_NUM= self.receiver_seq, \
                             ACK=1, FIN=0, DATA=b"").pack()
        self.socket.sendto(ack_segment, (self.dst_ip, self.dst_port))

        # print("data is",this_data)
        return segment

    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.
        # first, send a FIN
        fin_segment = Packet(SEQ_NUM=self.sender_seq, ACK_NUM=self.receiver_seq,\
                             ACK=0, FIN=1).pack()
        self.socket.sendto(fin_segment,(self.dst_ip, self.dst_port))
        self.sender_seq += 1

        self.self_half_closed = True

        # wait for ACK to arrive
        self.wait_for_ack(fin_segment)

        # wait for fin to arrive
        while not self.remote_half_closed:
            time.sleep(self.sleep_interval)

        # received remote fin, wait for another 2 seconds
        time.sleep(self.fin_wait_period)

        self.closed = True
        self.socket.stoprecv()
