import socket
import sys
import time
from packet import packet
import threading
from os import walk

BUFFER_SIZE = 1024
trackerAddress = sys.argv[1]
trackerPort = int(sys.argv[2])
minAliveTime = int(sys.argv[3])
fileDic = {}
peerNum = None
isFin = False
originFilename = ""

def listenForFile(UDPSocket, ackSocket):
    global peerNum
    global isFin
    
    while True:
        if isFin: break
        reversedMessage, serverAddress = UDPSocket.recvfrom(BUFFER_SIZE)
        ackPort, peerID, filename, chuck, data = packet.parse_udp_data(reversedMessage)
        if filename == "CLOSE":
            break
        if peerNum == None:
            peerNum = peerID
        elif peerNum != peerID:
            print("Send to wrong peer")
        if filename in fileDic:
            if chuck == len(fileDic[filename]):
                fileDic[filename].append(data)
        else:
            fileDic[filename] = []
            fileDic[filename].append(data)
        
        # ACK
        ackSocket.sendto(packet(5, "", 0, 0, peerID, filename, len(fileDic[filename]) - 1, "").get_udp_data(), (trackerAddress, ackPort))

def sendFile(UDPSocket):
    global isFin
    global originFilename
    while True:
        reversedMessage, serverAddress = UDPSocket.recvfrom(BUFFER_SIZE)
        IP, receiverPort, filename, chuck, peerID, ackPort = packet.parse_udp_data(reversedMessage)
        if filename == "CLOSE":
            isFin = True
            print("PEER " + str(peerNum) + " SHUTDOWN: HAS " + str(len(fileDic)))
            for fi in fileDic:
                print(str(peerNum) + "    " + fi)
                if fi != originFilename:
                    fw = open("../Shared/" + fi, "wb")
                    for data in fileDic[fi]:
                        fw.write(data)
                    fw.close()
            break
        else:
            for i in range(chuck, len(fileDic[filename])):
                UDPSocket.sendto(packet(2, "", 0, ackPort, peerID, filename, i, fileDic[filename][i]).get_udp_data(), (IP, receiverPort))

if __name__ == '__main__':
    # shake hands with tracker
    TCPSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    TCPSocket.connect((trackerAddress, trackerPort))
    # find current IP address
    hostname = socket.gethostname()    
    IPAddr = socket.gethostbyname(hostname)
    # create a port for peer to receive files
    receiveSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiveSocket.bind(("", 0))
    receiveSocketPortNum = receiveSocket.getsockname()[1]
    # create a port for peer to send files
    sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sendSocket.bind(("", 0))
    sendSocketPortNum = sendSocket.getsockname()[1]
    # get file name
    filename = []
    for (dirp, dir, filenames) in walk("../Shared/"):
        filename = filenames
    DS=-1
    nfs=-1
    for i in range(0, len(filename)):
        if filename[i] == ".DS_Store":
            DS = i
        elif filename[i].startswith(".nfs"):
            nfs = i
    if(DS!=-1):
        del filename[DS]
    if(nfs!=-1):
        del filename[nfs]
    filename = filename[0]
    # create chucks
    MAX_DATA_LENGTH = 512 - len(filename) - 12
    f = open("../Shared/" + filename, "rb")
    chuckID = 0
    originFilename = filename
    fileDic[filename] = []
    with open("../Shared/" + filename, 'rb') as f:
        message = f.read(MAX_DATA_LENGTH)
        while message:
            fileDic[filename].append(message) ###
            chuckID += 1
            message = f.read(MAX_DATA_LENGTH)
    # register
    TCPSocket.send(packet(1, IPAddr, sendSocketPortNum, receiveSocketPortNum, 0, filename, len(fileDic[filename]), minAliveTime).get_udp_data())
    ackSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    threading.Thread(target=sendFile, args=(sendSocket,)).start()
    threading.Thread(target=listenForFile, args=(receiveSocket,ackSocket,)).start()

