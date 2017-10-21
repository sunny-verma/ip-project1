# client.py

import socket                   # Import socket module

def client(s):
    with open('received_file', 'wb') as f:
        print 'file opened'
        while True:
            print('receiving data...')
            data = s.recv(1024)
            print('data=%s', (data))
            if not data:
                break
            # write data to a file
            f.write(data)

    f.close()
    print('Successfully get the file')
    s.close()
    print('connection closed')


def main():
    s = socket.socket()  # Create a socket object
    host = "127.0.0.1"  # Get local machine name
    port = 60000  # Reserve a port for your service.

    s.connect((host, port))
    s.send("Hello server!")
    client(s)

if __name__ == "__main__":
    main()
