
# this file is based on extra Resource in A2
class packet:

    def __init__(self, typ, IP, senderPort, receiverPort, peerID, filename, chuck, data):
        # type 1 is used for peer to tell tracker it's IP Address, sender Port ID, receiver Port ID, file name and number of chucks, time(data)
        # type 2 is used for peer to peer to transfer file data, include file name, chuck id and data
        # type 3 is used for tracker to tell peer the other peer's IP, Port and filename and chuck id
        # For type 3, if filename == "CLOSE", peer quit
        # type 4 is used for tracker to tell peer tracker's ACK port
        # type 5 is ACK, include, my id, filename and chuck id

        self.type = typ
        self.IP = IP
        self.senderPort = senderPort
        self.receiverPort = receiverPort
        self.peerID = peerID
        self.filename = filename
        self.chuck = chuck
        self.data = data

    def get_udp_data(self):
        array = bytearray()
        array.extend(self.type.to_bytes(length=4, byteorder="big"))
        if self.type == 1:
            array.extend(len(self.IP).to_bytes(length=4, byteorder="big"))
            array.extend(self.IP.encode())
            array.extend(self.senderPort.to_bytes(length=4, byteorder="big"))
            array.extend(self.receiverPort.to_bytes(length=4, byteorder="big"))
            array.extend(len(self.filename).to_bytes(length=4, byteorder="big"))
            array.extend(self.filename.encode())
            array.extend(self.chuck.to_bytes(length=4, byteorder="big"))
            array.extend(self.data.to_bytes(length=4, byteorder="big"))
        elif self.type == 2:
            array.extend(self.receiverPort.to_bytes(length=4, byteorder="big"))
            array.extend(self.peerID.to_bytes(length=4, byteorder="big"))
            array.extend(self.chuck.to_bytes(length=4, byteorder="big"))
            array.extend(len(self.filename).to_bytes(length=4, byteorder="big"))
            array.extend(self.filename.encode())
            array.extend(len(self.data).to_bytes(length=4, byteorder="big"))
            array.extend(self.data)
        elif self.type == 3:
            array.extend(len(self.IP).to_bytes(length=4, byteorder="big"))
            array.extend(self.IP.encode())
            array.extend(self.receiverPort.to_bytes(length=4, byteorder="big"))
            array.extend(len(self.filename).to_bytes(length=4, byteorder="big"))
            array.extend(self.filename.encode())
            array.extend(self.chuck.to_bytes(length=4, byteorder="big"))
            array.extend(self.peerID.to_bytes(length=4, byteorder="big"))
            array.extend(self.senderPort.to_bytes(length=4, byteorder="big"))
        elif self.type == 4:
            array.extend(len(self.IP).to_bytes(length=4, byteorder="big"))
            array.extend(self.IP.encode())
            array.extend(self.receiverPort.to_bytes(length=4, byteorder="big"))
        elif self.type == 5:
            array.extend(self.peerID.to_bytes(length=4, byteorder="big"))
            array.extend(self.chuck.to_bytes(length=4, byteorder="big"))
            array.extend(len(self.filename).to_bytes(length=4, byteorder="big"))
            array.extend(self.filename.encode())
        return array

    @staticmethod
    def parse_udp_data(UDPdata):
        typ = int.from_bytes(UDPdata[0:4], byteorder="big")
        if typ == 1:
            IPlength = int.from_bytes(UDPdata[4:8], byteorder="big")
            IP = UDPdata[8:8 + IPlength].decode()
            senderPort = int.from_bytes(UDPdata[8 + IPlength:12 + IPlength], byteorder="big")
            receiverPort = int.from_bytes(UDPdata[12 + IPlength:16 + IPlength], byteorder="big")
            filenameLen = int.from_bytes(UDPdata[16 + IPlength:20 + IPlength], byteorder="big")
            filename = UDPdata[20 + IPlength:20 + IPlength + filenameLen].decode()
            chuck = int.from_bytes(UDPdata[20 + IPlength + filenameLen:24 + IPlength + filenameLen], byteorder="big")
            time = int.from_bytes(UDPdata[24 + IPlength + filenameLen:28 + IPlength + filenameLen], byteorder="big")
            return IP, senderPort, receiverPort, filename, chuck, time
        elif typ == 2:
            ackPort = int.from_bytes(UDPdata[4:8], byteorder="big")
            peerID = int.from_bytes(UDPdata[8:12], byteorder="big")
            chuck = int.from_bytes(UDPdata[12:16], byteorder="big")
            filenameLen = int.from_bytes(UDPdata[16:20], byteorder="big")
            filename = UDPdata[20:20 + filenameLen].decode()
            dataLen = int.from_bytes(UDPdata[20 + filenameLen:24 + filenameLen], byteorder="big")
            data = UDPdata[24 + filenameLen:28 + filenameLen + dataLen]
            return ackPort, peerID, filename, chuck, data
        elif typ == 3:
            IPlength = int.from_bytes(UDPdata[4:8], byteorder="big")
            IP = UDPdata[8:8 + IPlength].decode()
            receiverPort = int.from_bytes(UDPdata[8 + IPlength:12 + IPlength], byteorder="big")
            filenameLen = int.from_bytes(UDPdata[12 + IPlength:16 + IPlength], byteorder="big")
            filename = UDPdata[16 + IPlength:16 + IPlength + filenameLen].decode()
            chuck = int.from_bytes(UDPdata[16 + IPlength + filenameLen:20 + IPlength + filenameLen], byteorder="big")
            peerID = int.from_bytes(UDPdata[20 + IPlength + filenameLen:24 + IPlength + filenameLen], byteorder="big")
            ackPort = int.from_bytes(UDPdata[24 + IPlength + filenameLen:28 + IPlength + filenameLen], byteorder="big")
            return IP, receiverPort, filename, chuck, peerID, ackPort
        elif typ == 4:
            IPlength = int.from_bytes(UDPdata[4:8], byteorder="big")
            IP = UDPdata[8:8 + IPlength].decode()
            receiverPort = int.from_bytes(UDPdata[8 + IPlength:12 + IPlength], byteorder="big")
            return IP, receiverPort
        elif typ == 5:
            peerID = int.from_bytes(UDPdata[4:8], byteorder="big")
            chuck = int.from_bytes(UDPdata[8:12], byteorder="big")
            filenameLen = int.from_bytes(UDPdata[12:16], byteorder="big")
            filename = UDPdata[16:16 + filenameLen].decode()
            return peerID, chuck, filename