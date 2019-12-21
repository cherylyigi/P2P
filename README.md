Code in python

In the beginning, each peer hold a single file with distint name it the Share directory. Tracker will keep track of each single file and make sure each peer get a copy of files hold by other peers.

Peer will stay alive for MIN ALIVE TIME after all the transitions finished

Please use the following to run the tracker
./tracker.sh
Use cat port.txt to find tracker's port number
Use the following to run the peer
./peer.sh [IP] [PORT] [MIN ALIVE TIME]

NOTICE:
when place tracker.py and peer.py in any directory, please copy packet.py along with them. Both file import packet.py as helper.

Thanks!:)
