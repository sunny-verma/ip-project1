# server.py

import socket                   # Import socket module
import platform
import json
import os
from threading import Thread
from peers.common import RFCs
import threading
# handle the threads in here
threads = []
LOCAL_RFC_LIST = []
RFC_PATH = None

def formulate_msg(msg, cookie=None, rfc=None):
    if msg == 'OK':
        MSG = "RESPONSE: 200 OK," + "\n" + "Found the File "
    elif msg == "Sent":
        MSG = "RESPONSE: 201 OK," + "\n" + "Sent the RFC succesfully " + str(rfc)
    elif msg == "None":
        MSG = "RESPONSE: 404," + "\n" + "Din't find the RFC "
    return MSG

import sys
class Server():
    def __init__(self, conn, ip, port, path):
        global RFC_PATH
        self.ip = ip
        self.port = port
        self.conn = conn
        self.data  = None
        RFC_PATH = path
        print RFC_PATH


class PeerServerHandleThread(threading.Thread):
    def __init__(self, conn, ip, port):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.conn = conn
        print "[+] New thread started for " + ip + ":" + str(port)



    def create_rfc_lsit_dict(self):
        global  LOCAL_RFC_LIST
        obj = []
        for k in LOCAL_RFC_LIST:
            a = {'rfcnumber': k.rfcnumber,
                 'title': k.title,
                 'present_list': k.present_list}
            obj.append(a)
        return obj

    def run(self):
        global LOCAL_RFC_LIST
        data = self.conn.recv(1024)
        command = data.split('\n')[0][:13]

        if command == "GET RFC-Index":
            print "peer request the GET RFC values"
            # Create the object as required
            # send it to client
            obj = self.create_rfc_lsit_dict()
            print obj
            print self.ip, self.port, self.conn
            self.send_response(obj)
        elif command[:8] == "GET RFC ":
            print "peer request the GET RFC values"
            rfc_number = int(data[8:10])
            self.sendfile(self.conn, rfc_number)
        self.conn.close()

    def send_response(self, data):
        self.conn.send(json.dumps(data))

    def sendfile(self, conn, rfc_number):
        exists, filename = self.check_rfc_exists_locally(rfc_number)
        if not exists or not os.path.exists(filename):
            print "What the hell you are trying to send!!"
            MSG = formulate_msg("None")
            conn.send(MSG)

            return
        MSG = formulate_msg("OK")
        conn.send(MSG)
        f = open(filename, 'rb')
        l = f.read(1024)
        while (l):
            conn.send(l)
            l = f.read(4096)
        f.close()
        print('Done sending!!')


    def check_rfc_exists_locally(self, rfc_number):
        file = 'RFC' + str(rfc_number) + '.txt'
        current_dir = os.getcwd()
        abs_path = os.path.join(os.path.join(os.path.join(current_dir, 'peers'), RFC_PATH), file)
        exists = os.path.exists(abs_path)
        if exists:
            return True, abs_path
        return False, None



import thread, threading


class MainServer():
    def __init__(self, path):
        global RFC_PATH
        RFC_PATH = path
        print RFC_PATH

    def run(self, host=None, port=None, path=None, local_rfc_list=None):
        global RFC_PATH, LOCAL_RFC_LIST
        print "I am in start server"
        try:
            tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcpsock.bind((host, port))
        except:
            _, _, tb = sys.exc_info()
            raise

        LOCAL_RFC_LIST = local_rfc_list
        RFC_PATH = path

        while True:
            tcpsock.listen(0)
            print "Waiting for incoming connections..."
            (conn, (ip, port)) = tcpsock.accept()
            newthread = PeerServerHandleThread(conn, ip, port)
            newthread.start()
            # newthread.run()
            threads.append(newthread)
            print 'Server listening....'
        for t in threads:
            t.join()

    def get_local_rfcs(self, number, port):

        title = "RFC %s About something",
        RFC = RFCs(1, title, ['127.0.0.1', port])
        LOCAL_RFC_LIST.append(RFC)
        return LOCAL_RFC_LIST


def main():
    server = MainServer().start(port=9001, path='peer1rfcs/', number = 1)


if __name__ == "__main__":
    main()