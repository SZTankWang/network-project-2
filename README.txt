Xining Yuan (xyz3860) part 1 & 2 & bonus


Zhenming Wang (zwg3064) part 3 & 4 & 5


Part 1: Chunking
Description:
	A function to cut data which is longer than 1472 in to different chunks.
	input: data_bytes
	result: send this chunk to the receiver.
Part 2: Reordering
Description:
	Add sequence numbers in both sender and receiver as an instant number in __init__ of class streamer to tolerance reordering. I also add a buffer dictionary in recv function to temporally save received data with its sequence number. In each iteration, I check if the expected receive sequence number exists in the buffer. If yes, I pop this data from buffer. If not, recv function will keep listening and receiving data. The steps are repeated until the bufer is empty.