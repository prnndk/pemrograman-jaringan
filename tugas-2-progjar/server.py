from socket import *
import socket
import threading
import logging
from datetime import datetime


def proses_string(request_string):
    balas = "ERROR: PESAN TIDAK SESUAI\r\n"
    if request_string.startswith("TIME") and request_string.endswith("\n"):
        now = datetime.now()
        waktu = now.strftime("%H:%M:%S")
        balas = f"JAM {waktu}\r\n"
    if request_string.startswith("QUIT") and request_string.endswith("\n"):
        balas = "END"
    return balas


class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        while True:
            data = self.connection.recv(32)
            if data:
                request_s = data.decode()
                balas = proses_string(request_s)
                if balas == "END":
                    logging.warning("[CLIENT] closing connection")
                    self.connection.close()
                    break
                self.connection.sendall(balas.encode())
            else:
                break
        self.connection.close()


class Server(threading.Thread):
    def __init__(self):
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

    def run(self):
        try:
            self.my_socket.bind(('0.0.0.0', 45000))
            self.my_socket.listen(1)
            while True:
                self.connection, self.client_address = self.my_socket.accept()
                logging.warning(f"connection from {self.client_address}")

                clt = ProcessTheClient(self.connection, self.client_address)
                clt.start()
                self.the_clients.append(clt)
        except Exception as e:
            logging.error(e)
            self.my_socket.close()


def main():
    svr = Server()
    svr.start()


if __name__ == "__main__":
    main()
