import socket
from threading import Thread
from SocketServer import ThreadingMixIn
import time
import sys
import json
import threading, thread
############ Global Variables ###################

# handle the threads in here
threads = []

# save the registerd clients info here
RS_DICT = {}

# This code has to be removed
'''
RS_DICT = {('127.0.0.1', 1237): {'hostname': 'Peer4', 'activation_stats': 1, 'peer_server_portnumber': 1237, 'flag': False, 'cookie': 1001, 'time': 1508799811.359, 'ttl': None},
('127.0.0.1', 1236): {'hostname': 'Peer3', 'activation_stats': 1, 'peer_server_portnumber': 1236, 'flag': True, 'cookie': 1001, 'time': 1508799811.359, 'ttl': None},
('127.0.0.1', 1235): {'hostname': 'Peer2', 'activation_stats': 1, 'peer_server_portnumber': 1235, 'flag': True, 'cookie': 1001, 'time': 1508799811.359, 'ttl': None},
('127.0.0.1', 1234): {'hostname': 'Peer1', 'activation_stats': 1, 'peer_server_portnumber': 1234, 'flag': True, 'cookie': 1002, 'time': 1508799811.359, 'ttl': None}}
'''
# Lock
lock = threading.RLock()

# RS server port info
TCP_IP = '0.0.0.0'
TCP_PORT = 65432
# BUFFER_SIZE = 20  # Normally 1024, but we want fast response

# local variables
cookie_number = 1000


# MSG
def formulate_msg(msg, cookie = None):
    if msg == 'OK':
        MSG = "RESPONSE: 200 OK," + "\n" + "Cookie: " + cookie
    if msg == 'None':
        MSG = "RESPONSE: 404," + "\n" + "Din't find the RFC "

######## Helper methods #################3

def generate_cookie():
    global  cookie_number
    with lock:
        cookie_number = cookie_number + 1
    return cookie_number

def get_entry_from_RS_DICT(tuple):
    global RS_DICT
    return RS_DICT.get(tuple)


def set_entry_from_RS_DICT(tuple , value):
    global RS_DICT
    with lock:
        RS_DICT[tuple] = value
    print RS_DICT

def update_key_from_RS_DICT(tuple , key, value):
    global RS_DICT
    if tuple is None:
        print "This value doesn't exists"
        return False
    exists = RS_DICT.get(tuple)
    if not exists:
        print "This value doesn't exists"
        return False
    with lock:
        RS_DICT[tuple][key] = value
    print RS_DICT
    return True

def delete_entry_from_RS_DICT(tuple):
    global  RS_DICT
    with lock:
        del RS_DICT[tuple]

class Handle_Timer():
    pass

time_interval = 0

def change_flag_entry(ip=None, port=None):
    global RS_DICT, time_interval
    tuple = (ip,port)
    while True:
        print "Starting timer for this entry"
        time.sleep(7200)
        if time_interval == 0:
            time_interval =+1
            return
        with lock:
            RS_DICT[tuple]["flag"] = False


def convert_data_to_client_info(data, tuple):
    global  RS_DICT

    data = {"cookie": generate_cookie(),
            "hostname" : data.get("hostname"), # the hostname of the peer
            "flag" : True, #  indicates whether the peer is currently active
            "ttl": 7200, # timer for the entry
            "peer_server_portnumber": data.get("peer_server_portnumber"), # to which the RFC server of this peer is listening
            "activation_stats" : 1, #  the number of times this peer has been active
            "time": time.time() # the most recent time/date that the peer registered.
    }

    thread.start_new_thread(change_flag_entry, (tuple))
    return data


class RSClientHandleThread(Thread):
    def __init__(self, conn, ip, port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.conn = conn
        self.data  = None


        print "[+] New thread started for " + ip + ":" + str(port)

    def run(self):

        data = str(self.conn.recv(9096))
        # data = json.dumps({'action': 'Register'})
        # self.data = json.loads(data)
        print "received data is :", self.data

        # Cases
        if data[:8] == "Register":
            # 1. Register
            print "I am in register case"
            data = self.conn.recv(4096)
            if data:
                self.data = json.loads(data)
            else:
                print "Unable to register with the client"

            self.Register()

        elif data[:6]  == "PQuery":
            # 2. PQuery
            print "I am in PQuery case"
            self.PQuery()



        elif data[:5] == "Leave":
            # 3. Leave
            print "I am leaving case"
            data = self.conn.recv(4096)
            if data:
                self.data = json.loads(data)
            else:
                print "MSG received was wrong for leaving"
            self.Leave()

        elif data[:9] == "KeepAlive":
            # 4. KeepAlive
            self.KeepAlive()

    def send_response(self, data):
        self.conn.send(json.dumps(data))

    def create_RS_DICT(self, tuple):
        set_entry_from_RS_DICT(tuple, convert_data_to_client_info(self.data, tuple))


    def Register(self):
        tuple = (self.ip, self.data.get("peer_server_portnumber"))

        # 1. Check if the data has cookie value already set ?
        entry_exists = get_entry_from_RS_DICT((self.ip, self.port))

        if entry_exists:
            ## if yes, then update the rest of dict value
            self.update_RS_DICT(tuple)
        else:
            ## if no, then craete new entry in the registration query
            self.create_RS_DICT(tuple)
        respose = str ("Status: 200 OK, cookie: %s " % int(RS_DICT[tuple].get('cookie')))
        self.send_response(respose)



    def get_active_peers(self):
        global RS_DICT
        print RS_DICT
        active_peers = []
        for key, value in RS_DICT.items():
            for k, v in value.items():
                if value['flag']:
                    active_peers.append({"hostname": value.get("hostname"),
                                   "peer_server_portnumber": value.get('peer_server_portnumber')})
                    break
        return active_peers

    def PQuery(self):
        active_peers = self.get_active_peers()
        if active_peers:
            data = active_peers
            print "Active Peer list", active_peers
        else:
            print "No active peers found in the RS server"
            data = "404!! Not found"
        self.send_response(data)

    def Leave(self):
        cookie = int(self.data)
        tuple, value = self.find_tuple(cookie)
        ret = update_key_from_RS_DICT(tuple, 'flag', False)
        if not ret:
            print "Status: 404 Not Found"


            return
        respose = str("Status: 200 OK, Marked Peer as inactive")
        self.send_response(respose)


    def KeepAlive(self):
        data = str(self.conn.recv(1000))
        print "Keep Alive Triggered"
        print "Cookie Number is %s" % data
        cookie_number = int(data)
        tuple, value = self.find_tuple(cookie_number)
        if value is None:
            return
        update_key_from_RS_DICT(tuple, 'flag', True)
        update_key_from_RS_DICT(tuple, 'activation_stats', RS_DICT[tuple]["activation_stats"] + 1)
        update_key_from_RS_DICT(tuple, 'ttl', 7200)
        update_key_from_RS_DICT(tuple, 'time', time.time())


    def find_tuple(self, cookie):
        global RS_DICT
        for k, v in RS_DICT.items():
            if v.get("cookie") == cookie:
                return k, v
        return None, None


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
