import math
import struct
import socket
import select
import threading

_HOST = '127.0.0.1'
_PORT = 10000

class ChatServer(threading.Thread):
    #define server as thread
    MAX_WAITING_CONNECTIONS = 10
    RECV_BUFFER = 4096
    RECV_MSG_LEN = 4
    
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.connections = []
        self.running = True
    def _bind_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.MAX_WAITING_CONNECTIONS)
        self.connections.append(self.server_socket)
        #may brake(how does work)
        
    def _send(self, sock, msg):
        msg = struct.pack('>I', len(msg)) + msg
        sock.send(msg)
    
    def _receive(self, sock):
        data = None
        tot_len = 0 
        while tot_len < self.RECV_MSG_LEN:
            msg_len = sock.recv(self.RECV_MSG_LEN)
            tot_len += len(msg_len)
        
        if msg_len:
            data = ''
            msg_len = struct.unpack('>I', msg_len)[0]
            tot_data_len = 0
            while tot_data_len < msg_len:
                chunk = sock.recv(self.RECV_BUFFER)
                if not chunk:
                    data = None
                    break
            else:
                data += chunk
                tot_data_len += len(chunk)
        return data
    def _broadcast(self, client_socket, client_message):
        for sock in self.connections:
            is_not_the_server = sock != self.server_socket
            is_not_the_client_sending = sock != client_socket
            if is_not_the_server and is_not_the_client_sending:
                try:
                    self._send(sock, client_message)
                except socket.error:
                    sock.close()
                    self.connections.remove(sock)
    def _run(self):
        while self.running:
            try:
                ready_to_read, ready_to_write, in_error = select.select(self.connections, [], [], 60)
            except socket.error:
                continue
            else:
                for sock in ready_to_read:
                    if sock == self.server_socket:
                        try:
                            client_socket, client_address = self.server_socket.accept()
                        except socket.error:
                            break
                        else:
                            self.connections.append(client_socket)
                            print "Client (%s, %s) connected" % client_address
                            self._broadcast(client_socket, "\n[%s,%s] entered the chat room\n" % client_address)
                    else:
                        try:
                            data = self._recieve(sock)
                            if data:
                                self._broadcast(sock, "\r" + '<' + str(sock.getpeername()) + '>' + data)
                        except socket.error:
                            self._broadcast(sock, "\nClient (%s, %s) is offline\n" % client_address)
                            print "Client (%s, %s) is offline" % client_address
                            sock.close()
                            self.connections.remove(sock)
                            continue
        self.stop()

    def run(self):
        self._bind_socket()
        self._run()
        
    def stop(self):
        self.running = False
        self.server_socket.close()

def main():
    chat_server = ChatServer(_HOST, _PORT)
    chat_server.start()

if __name__ == '__main__':
    main()