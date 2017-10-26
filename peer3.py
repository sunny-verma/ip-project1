from peers.client_common import Client
from peers.server_common import MainServer
import threading, thread
import socket
from peers.common import RFCs
port_server = 9003
peer_folder = 'peer3rfcs'
threads = []
local_rfc_list = []
# Comment these value for TASK1
# This is required for Task2
for x in range(21, 31):
    global local_rfc_list
    title = "RFC %s About something" % x
    RFC = RFCs(x, title, ['127.0.0.1', port_server])
    local_rfc_list.append(RFC)

print local_rfc_list
## Till Here

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
    thread1 = myThread(1, "Thread-1", 1, 1)
    thread2 = myThread(1, "Thread-2", 1, 2)
    thread1.start()
    thread2.start()

if __name__ == "__main__":
    main()