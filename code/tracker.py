import socket
import sys
from packet import packet
import threading
import queue
import time

BUFFER_SIZE = 1024
newPeerPort = 0
IPAddr = ""

peerDic = {} # id: [IP, comute with track port, receive port, totaltime, waitstart]
fileOwner = {} # dictory, file name: list of [peer id, end chuck id]
peerWants = [] # list of dic, index is peer id, dictory (file name: [start chuck, end chuck id (number - 1)])
currFiles = [] # list of [filename, chuck number]
busyQueue = queue.Queue(maxsize=10)
isEnd = False
nowID = 0
trackerlock = threading.Lock()

def peerConnection(newpeerSocket):
    global peerDic
    global fileOwner
    global peerWants
    global currFiles
    global busyQueue
    global nowID
    while not isEnd:
        # wait for connecting
        newpeerSocket.listen(1)
        if isEnd: break
        conn, addr = newpeerSocket.accept()
        if isEnd: break
        reversedMessage, senderAddress = conn.recvfrom(BUFFER_SIZE)
        # tell peer which 
        IP, senderPort, receiverPort, filename, chuck, time = packet.parse_udp_data(reversedMessage)
        if filename == "CLOSE":
            break
        # assign a new id to peer
        trackerlock.acquire()
        peerInfo = [IP, senderPort, receiverPort, time, None]
        newId = nowID
        nowID += 1
        # reset wait time
        for key in peerDic:
            peerDic[key][4] = None
        peerDic[newId] = peerInfo
        # add new file to peer wants
        for peer in peerWants:
            peer[filename] = [0, chuck-1] ###
        # add all exsiting files to peerWants
        newWant = {}
        for F in currFiles:
            newWant[F[0]] = [0, F[1]-1]
        peerWants.append(newWant)
        # add new file to currFiles
        currFiles.append([filename, chuck])
        # update file owner
        fileOwner[filename] = []
        fileOwner[filename].append([newId, chuck-1])
        # update busy Queue
        busyQueue.put(newId)
        print("PEER " + str(newId) + " CONNECT: OFFERS 1")
        print(str(newId) + "    " + filename + " " + str(chuck))
        trackerlock.release()

def ackConnection(ackSocket):
    global fileOwner
    global peerWants
    while not isEnd:
        # wait for connecting
        reversedMessage, serverAddress = ackSocket.recvfrom(BUFFER_SIZE)
        peerID, chuck, filename = packet.parse_udp_data(reversedMessage)
        if filename == "CLOSE": break
        #trackerlock.acquire()
        preStart = peerWants[peerID][filename][0]
        if (chuck + 1) > preStart:
            print("PEER " + str(peerID) + " ACQUIRED: CHUNK " + str(chuck + 1) + "/" + str(peerWants[peerID][filename][1] + 1) + " " + filename)
            peerWants[peerID][filename][0] = chuck + 1
            isFind = False
            for pair in fileOwner[filename]:
                if pair[0] == peerID:
                    pair[1] = chuck
                    isFind = True
            if not isFind:
                newPair = [peerID, 0]
                fileOwner[filename].append(newPair)
        #trackerlock.release()

def giveWants(wantsSocket, ackSocketPortNum):
    global peerDic
    global fileOwner
    global peerWants
    global currFiles
    global busyQueue
    global isEnd
    global newPeerPort
    global IPAddr
    while not isEnd:
        isFin = True
        time.sleep(1)
        trackerlock.acquire()
        for i in range(0, len(peerWants)):
            if not i in peerDic: continue
            # check all files peer i wants
            for filename in peerWants[i]:
                nextChuck = peerWants[i][filename][0]
                if nextChuck > peerWants[i][filename][1]:
                    continue
                else:
                    isFin = False
                    # get all owners that satidfied
                    ownerList = []
                    for owner in fileOwner[filename]:
                        if owner[1] >= peerWants[i][filename][0]:
                            ownerList.append(owner[0])
                    if len(ownerList) == 0:
                        print ("ownerList is empty")
                    # choose a owner to send packet
                    candidate = busyQueue.get()
                    while not candidate in ownerList:
                        busyQueue.put(candidate)
                        candidate = busyQueue.get()
                    # let candidate send it
                    candidateIP = peerDic[candidate][0]
                    candidatePort = peerDic[candidate][1]
                    # use sender's port to store ack port
                    wantsSocket.sendto(packet(3, peerDic[i][0], ackSocketPortNum, peerDic[i][2], i, filename, nextChuck, "").get_udp_data(), (candidateIP, candidatePort))
                    busyQueue.put(candidate)
        now = time.time()
        if isFin:
            deleteIds = []
            for idkey in peerDic:
                if peerDic[idkey][4] == None:
                    peerDic[idkey][4] = now
                elif now - peerDic[idkey][4] > peerDic[idkey][3]:
                    # tell peer to close
                    wantsSocket.sendto(packet(3, "", 0, 0, 0, "CLOSE", 0, "").get_udp_data(), (peerDic[idkey][0], peerDic[idkey][1]))
                    wantsSocket.sendto(packet(2, "", 0, 0, 0, "CLOSE", 0, "").get_udp_data(), (peerDic[idkey][0], peerDic[idkey][2]))
                    deleteIds.append(idkey)
                    print("PEER " + str(idkey) + " DISCONNECT: RECEIVED " + str(len(currFiles)))
                    for fi in currFiles:
                        print(str(idkey) + "    " + fi[0])
            for dId in deleteIds:
                del peerDic[dId]
                for filename in fileOwner:
                    for pair in fileOwner[filename]:
                        if pair[0] == dId:
                            fileOwner[filename].remove(pair)
                            break
                if len(peerDic) == 0:
                    isEnd = True
                    trackerlock.release()
                    TCPSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    TCPSocket.connect((IPAddr, newPeerPort))
                    TCPSocket.send(packet(1, "", 0, 0, 0, "CLOSE", 0, 0).get_udp_data())
                    wantsSocket.sendto(packet(5, "", 0, 0, 0, "CLOSE", 0, "").get_udp_data(), (IPAddr, ackSocketPortNum))
                    return
        trackerlock.release()            

if __name__ == '__main__':
    # find current IP address
    hostname = socket.gethostname()    
    IPAddr = socket.gethostbyname(hostname)
    # create server socket
    newpeerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Choose a free port and write to a file
    newpeerSocket.bind(("", 0))
    newPeerPort = newpeerSocket.getsockname()[1]
    portFile = open("../port.txt", "w")
    portFile.write(str(newPeerPort))
    #print("server port is " + str(newPeerPort))
    portFile.close()
    # create a tcp used for ack
    ackSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # assign a port to socket
    ackSocket.bind(("", 0))
    ackSocketPortNum = ackSocket.getsockname()[1]
    threading.Thread(target=peerConnection, args=(newpeerSocket,)).start()
    # create a new thread for ack
    threading.Thread(target=ackConnection, args=(ackSocket,)).start()
    # create a new thread for peer wants
    wantsSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    threading.Thread(target=giveWants, args=(wantsSocket, ackSocketPortNum,)).start()

    
