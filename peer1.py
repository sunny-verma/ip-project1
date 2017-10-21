from peer.client_p0 import main as client_main
from peer.server_p0 import main as server_main
import threading


def main():
    ClientThread = threading.Thread(client_main()).start()
    ServerThread = threading.Thread(server_main().start())
    ClientThread.join()
    ServerThread.jon()

if __name__ == "__main__":
    main()