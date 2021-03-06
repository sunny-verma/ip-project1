from peers.client_common import Client
from peers.server_common import MainServer
import threading, thread
import socket
from peers.common import RFCs
port_server = 9001
peer_folder = 'peer1rfcs'
threads = []
local_rfc_list = []

# Comment out this for Task1
'''
for x in range(1, 61):
    global local_rfc_list
    title = "RFC %s About something" % x
    RFC = RFCs(x, title, ['127.0.0.1', port_server])
    local_rfc_list.append(RFC)
'''

# Comment these value for TASK1

# This is required for Task2
for x in range(1, 11):
    global local_rfc_list
    title = "RFC %s About something" % x
    RFC = RFCs(x, title, ['127.0.0.1', port_server])
    local_rfc_list.append(RFC)
## Till Here

print local_rfc_list
client = Client("127.0.0.1", 65432, port_server=port_server, hostname="127.0.0.1", path=peer_folder, local_rfc_list=local_rfc_list)
server = MainServer(path=peer_folder)

class myThread (threading.Thread):
   def __init__(self, threadID, name, counter, which):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
      self.which = which

   def run(self):
      print "Starting " + self.name
      if self.which == 1:
          client.run()
      else:
          server.run("127.0.0.1", port_server, peer_folder, local_rfc_list)
      print "Exiting " + self.name

def main():
    thread1 = myThread(1, "Client Thread", 1, 1)
    thread2 = myThread(1, "Server Thread", 1, 2)
    thread1.start()
    thread2.start()

if __name__ == "__main__":
    main()