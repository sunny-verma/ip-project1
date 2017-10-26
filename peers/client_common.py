# client.py
import socket                   # Import socket module
import platform
import json
import threading, thread
import os
from peers.common import RFCs
import time
import pickle
cumulative_time = 0
RESGISTER  = "Register"
PQuery = "PQuery"
RFCQuery = "RFCQuery"
GETRFC = "GETRFC"
LOCAL_RFC_LIST = []
RFC_PEER_LIST = []
RFC_PATH = None
cookie = 0
downloaded_file_path = None
active_peer_list = []

def formulate_msg(msg, host=None, rfcnumber=None):
    if msg == RFCQuery:
        MSG = 'GET RFC-Index P2P-DI/1.0' + "\n" + "HOST: " + host + "\n" + "OS: " + platform.system()
    elif msg == GETRFC:
        MSG = "GET RFC %s P2P-DI/1.0" % str(rfcnumber) + "\n" + "HOST:" + host + "\n" + "OS:" + platform.system() + "\n"
    return MSG


class Client(object):
    def __init__(self, host=None, port=None, port_server=None, hostname = None, path=None, local_rfc_list=None):
        global LOCAL_RFC_LIST, RFC_PATH

        self.host = "127.0.0.1" if host is None else host  # Get local machine name
        self.port = 65432 if port is None else port # Reserve a port for your service.
        self.port_server = "9001" if port_server is None else port_server # for your server
        self.hostname = hostname


        print "Hello client is connecting to RS server!"
        LOCAL_RFC_LIST = local_rfc_list
        RFC_PATH = path

    def run(self):
        global cookie
        # Here there will be Keep Alive MSG

        while(True):
            cin = raw_input("What you want to do today? \n"
                            "Enter 1 for Registering your peer: \n"
                            "Enter 2 for Leaving the P2P-DI system: \n"
                            "Enter 3 for Just PQuery from RS Server: \n"
                            "Enter 4 for Just RFCQuery from Active Peers: \n"
                            "Enter 5 for All downloading the RFCs: \n")

            if cin:
                print "User choose  %s " % cin
                # RFC query
                if str(cin) == '1':
                    print "Now we will connect to RS Server and register ourself."
                    s = socket.socket()  # Create a socket object
                    s.connect((self.host, self.port))
                    print "Connected"
                    my_port_number = self.port_server
                    MSG = "Register Peer"

                    s.send(MSG)
                    time.sleep(1)
                    info = {"hostname": self.hostname,
                            "peer_server_portnumber": my_port_number}
                    data = json.dumps(info)
                    s.send(data)
                    server_received_data = s.recv(1024)
                    if server_received_data:
                        print "Server sent %s" % str(server_received_data)
                        cookie = server_received_data.split(",")[1][9:13]
                        print "Client got cookie : %s from the server" % cookie
                    s.close()
                    #TODO(sunnyve ) Handle this later
                    thread.start_new_thread(self.send_keep_alive_to_rs)

                # self.RFCQuery(cin)
                elif str(cin) == '2':
                    print "Now Peer wants to leave the connection"
                    s = socket.socket()  # Create a socket object
                    try:
                        s.connect((self.host, self.port))
                    except:
                        print "Server is not Online"
                    MSG = "Leave Peer"
                    s.send(MSG)
                    time.sleep(1)
                    s.send(str(cookie))
                    time.sleep(1)
                    server_received_data = s.recv(1024)
                    if server_received_data:
                        print "Server sent %s" % str(server_received_data)
                    s.close()
                elif str(cin) == '3':
                    print "Peer want to do PQuery\n "
                    self.PQuery()

                elif str(cin) == '4':
                    self.RFCQuery()
                    time.sleep(1)

                elif str(cin) == '5':
                    start = time.clock()
                    self.download_the_rfcs()
                    end = time.clock() - start
                    print "Total Time Taken", end
                else:
                    print "Enter the valid value please [1-5] only"

            print "\n"


    def get_rfc_from_peers(self, active_peer_list):
        r = []
        global RFC_PEER_LIST, LOCAL_RFC_LIST
        print "Initially : ", RFC_PEER_LIST, LOCAL_RFC_LIST
        print "\n"
        # {"hostname": value.get("hostname"), "peer_server_portnumber": value.get('peer_server_portnumber')}
        for k in active_peer_list:
            if int(self.port_server) != int(k.get('peer_server_portnumber')):
                rfcs = self.ask_peer_rfc_list(k)
                r = r + rfcs
        RFC_PEER_LIST = LOCAL_RFC_LIST + r
        print "Finally RFC LIST : ", RFC_PEER_LIST
        print "Finally LOCALRFC LIST : ", LOCAL_RFC_LIST
        print "\n"

    def ask_peer_rfc_list(self, peer_info):
        global RFC_PEER_LIST
        peer_hostname = peer_info.get('hostname')
        peer_port = peer_info.get('peer_server_portnumber')
        s = socket.socket()
        s.connect((peer_hostname, int(peer_port)))
        MSG = formulate_msg(RFCQuery, self.hostname)

        s.send(MSG)

        # get the RFC list
        server_received_data = s.recv(10000)
        time.sleep(1)

        peer_list = json.loads(server_received_data)
        peer_l2 = []
        for k in peer_list:
            rfc = RFCs( k.get('rfcnumber'),k.get('title'), k.get('present_list')[0])
            peer_l2.append(rfc)

        peer_list = peer_l2
        if peer_list:
            for k1 in peer_list:
                for k2 in LOCAL_RFC_LIST :
                    if k1.rfcnumber == k2.rfcnumber:
                        k2.add_peer(k1.peer)
                        peer_list.remove(k1)
        s.close()
        return peer_list



    def check_rfc_exists_locally(self, rfc_number):
        global downloaded_file_path
        file = 'RFC' + str(rfc_number) + '.txt'
        current_dir = os.getcwd()
        abs_path = os.path.join(os.path.join(os.path.join(current_dir, 'peers'), RFC_PATH), file)
        exists = os.path.exists(abs_path)
        downloaded_file_path = abs_path
        if exists:

            return True, abs_path
        return False, None


    def send_keep_alive_to_rs(self):
        global cookie
        while True:
            time.sleep(300)
            print "Sending KeepAlive MSG  \n"
            MSG = "KeepAlive peer"
            s = socket.socket()
            s.connect((self.host, self.port))
            s.send(MSG)
            time.sleep(1)
            s.send(int(cookie))
            s.close()

    def handle_rfc_from_rs_server(self):
        s = socket.socket()
        s.connect((self.host, self.port))
        MSG = "PQuery Peer"
        s.send(MSG)
        time.sleep(1)
        data = s.recv(1024)
        active_peer_list = json.loads(data)
        if "404" in active_peer_list:
            print active_peer_list
            return None
        else:
            return active_peer_list


    def PQuery(self):
        global active_peer_list
        # If not present, Sending the RS Server with RFC Query
        # This method is to send to RFC server
        print "Now client will connect to server and ask for Active Peer list"
        active_peer_list = self.handle_rfc_from_rs_server()
        print active_peer_list
        if active_peer_list is None:
            print " OOPs!! No peer found! :( :("
            return None
        else:
            # Go to each peer
            return active_peer_list


    def print_peer_list(self):
        print "Printing all the RFCs"
        for k in RFC_PEER_LIST:
            print k.rfcnumber
            print k.title
            print k.present_list

    def RFCQuery(self, rfc_number=None):
        global RFC_PEER_LIST, active_peer_list
        # GET RFC from all the peers in the list and keep adding them

        self.get_rfc_from_peers(active_peer_list)

        # Search from the list and pick one  peer if it's present

    def download_the_rfcs(self):
        count_file_sent = 0
        global RFC_PEER_LIST, cumulative_time
        time_cum = 0
        print "downloading the file from peers"
        for k in RFC_PEER_LIST:
            if int(self.port_server) != int(k.present_list[0][1]):
                if count_file_sent < 50:
                    print "Downloading RFC # %s, PeerIP: %s PeerPort", (k.rfcnumber, k.present_list[0][0], int(k.present_list[0][1]))
                    self.get_the_file(k.present_list[0][0], int(k.present_list[0][1]), k.rfcnumber)
                    count_file_sent = count_file_sent + 1
                    time_cum = time_cum + cumulative_time
                    print "Count : ", count_file_sent
                    print "cumulative time taken: ", time_cum


    def LOCALRFCLIST(self, rfclist):
        global RFCLIST
        RFCLIST.update(rfclist)


    def get_the_file(self, peer_ip, peer_port, rfc_number):
        global downloaded_file_path, cumulative_time
        print "In the get method"
        s = socket.socket()
        s.connect((peer_ip, peer_port))
        MSG = formulate_msg(GETRFC, rfcnumber=rfc_number, host=self.hostname )
        s.send(MSG)
        does_rfc_exists = s.recv(1024)
        print "Received  : %s" % does_rfc_exists
        if "404" in does_rfc_exists:
            print "This Peer doesn't have this file."
            return
        if "200" in does_rfc_exists:
            print "This Peer does have this file. Now it will send the file"

        file = 'RFC' + str(rfc_number) + '.txt'
        current_dir = os.getcwd()
        downloaded_file_path = os.path.join(os.path.join(os.path.join(current_dir, 'peers'), RFC_PATH), file)
        print "downloaded_file_path ",  downloaded_file_path
        start = time.clock()
        with open(downloaded_file_path, 'wb') as f:
            print 'file opened'
            while True:
                data = s.recv(1024)
                if not data:
                    break
                # write data to a file
                f.write(data)
        f.close()

        print('Successfully got the file')
        end =  time.clock() - start
        print "Time Taken to download one file is ", end
        cumulative_time = end
        s.close()
        print 'connection closed'



def main():
    client = Client("127.0.0.1", 65432, hostname="Peer1")
    client.TASK()


if __name__ == "__main__":
    main()
