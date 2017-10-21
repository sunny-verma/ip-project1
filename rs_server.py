import socket
from threading import Thread
from SocketServer import ThreadingMixIn
import time
import sys
import json
import threading
############ Global Variables ###################

# handle the threads in here
threads = []

# save the registerd clients info here
RS_DICT = {}

# Lock
lock = threading.RLock()

# RS server port info
TCP_IP = '0.0.0.0'
TCP_PORT = 65432
# BUFFER_SIZE = 20  # Normally 1024, but we want fast response

# local variables
cookie_number = 1000


######## Helper methods #################3

def generate_cookie():
    global  cookie_number
    with lock:
        cookie_number = cookie_number + 1
    return cookie_number

def get_entry_from_RS_DICT(tuple):
    global RS_DICT
    return RS_DICT.get(tuple)


def dset_entry_from_RS_DICT(tuple , value):
    global RS_DICT
    with lock:
        RS_DICT[tuple] = value

def delete_entry_from_RS_DICT(tuple):
    global  RS_DICT
    with lock:
        del RS_DICT[tuple]

class Handle_Timer():
    pass

time_interval = 0
def handle_timer(tuple):
    t = threading.Timer(7200, change_flag_entry(tuple)).start()

def change_flag_entry():
    global RS_DICT, time_interval
    if time_interval == 0:
        time_interval =+1
        return
    with lock:
        RS_DICT[tuple]["flag"] = False


def convert_data_to_client_info(data):

    data = {"cookie": generate_cookie(),
            "hostname" : data.get("hostname"), # the hostname of the peer
            "flag" : True, #  indicates whether the peer is currently active
            "ttl": handle_timer(tuple), # timer for the entry
            "peer_server_portnumber": data.get("peer_server_portnumber"), # to which the RFC server of this peer is listening
            "activation_stats" : 1, #  the number of times this peer has been active
            "time": time.time() # the most recent time/date that the peer registered.
            }
    return data


class RSClientHandleThread(Thread):
    def __init__(self, conn, ip, port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.conn = conn


        print "[+] New thread started for " + ip + ":" + str(port)

    def run(self):

        data = self.conn.recv(9096)
        data = json.dumps({'action': 'Register'})
        self.data = json.loads(data)
        print "received data is :", self.data

        # Cases
        if self.data.get("action") == "Register":

            # 1. Register
            self.Register()
            return

        if self.data.get("action") == "PQuery":
            # 2. PQuery
            self.PQuery()
            return

        if self.data.get("action") == "Leave":
            # 3. Leave
            self.Leave()
            return

        if self.data.get("action") == "KeepAlive":
            # 4. KeepAlive
            self.KeepAlive()
            return

    def send_response(self, data):
        self.conn.send(json.dumps(data))

    def create_RS_DICT(self, tuple):
        set_entry_from_RS_DICT(tuple, convert_data_to_client_info(self.data, tuple))

    def update_RS_DICT(self, tuple):
        global  RS_DICT
        RS_DICT[tuple]["activation_stats"] = RS_DICT[tuple]["activation_stats"] + 1
        RS_DICT[tuple]["ttl"] = threading.Timer(7200, change_flag_entry(tuple))
        RS_DICT[tuple]["time"] = time.time()
        print "DICT", RS_DICT

    def Register(self):
        tuple = (self.ip, self.port)

        # 1. Check if the data has cookie value already set ?
        entry_exists = get_entry_from_RS_DICT((self.ip, self.port))

        if entry_exists:
            ## if yes, then update the rest of dict value
            self.update_RS_DICT(tuple)
        else:
            ## if no, then craete new entry in the registration query
            self.create_RS_DICT(tuple)
        respose = {"status" : "OK",
                   "cookie" : get_entry_from_RS_DICT(tuple)}
        self.send_response(respose)



    def get_active_peers(self):
        active_peers = []
        for key, value in RS_DICT:
            for k, v in value:
                if v == True:
                    active_peer = {"hostname": v.get("hostname"),
                                   "peer_server_portnumber": v.get('peer_server_portnumber')}
        return active_peers

    def PQuery(self):
        active_peers = self.get_active_peers()
        self.send_response(json.dumps(active_peers))

    def Leave(self):
        tuple = (self.ip, self.port)
        delete_entry_from_RS_DICT(tuple)

    def KeepAlive(self):
        tuple = (self.ip, self.port)
        self.update_RS_DICT(tuple)


def RSServer():
    try:
        tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcpsock.bind((TCP_IP, TCP_PORT))
    except:
        _, _, tb = sys.exc_info()
        raise

    while True:
        tcpsock.listen(0)
        print "Waiting for incoming connections..."
        (conn, (ip, port)) = tcpsock.accept()
        newthread = RSClientHandleThread(conn, ip, port)
        newthread.start()
        threads.append(newthread)


def main():
    RSServer()
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
