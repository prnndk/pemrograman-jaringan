from socket import *
import socket
import threading
import logging

from file_protocol import  FileProtocol
fp = FileProtocol()

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        command_buffer = ""
        while True:
            try:
                data = self.connection.recv(4096)
                if data:
                    d = data.decode()
                    command_buffer += d
                    if "\r\n\r\n" in command_buffer:
                        complete_command, _, rest_of_buffer = command_buffer.partition("\r\n\r\n")
                        command_buffer = rest_of_buffer
                        hasil = fp.proses_string(complete_command.strip())
                        hasil = hasil + "\r\n\r\n"
                        self.connection.sendall(hasil.encode())
                else:
                    break
            except BrokenPipeError:
                logging.warning(f"Client {self.address} closed the connection unexpectedly")
                break
            except Exception as e:
                logging.error(f"Unexpected error with client {self.address}: {e}")
                break
        self.connection.close()

class Server(threading.Thread):
    def __init__(self,ipaddress='0.0.0.0',port=8889):
        threading.Thread.__init__(self)
        self.ipinfo=(ipaddress,port)
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        try:
            logging.warning(f"server berjalan di ip address {self.ipinfo}")
            self.my_socket.bind(self.ipinfo)
            self.my_socket.listen(5)
            while True:
                self.connection, self.client_address = self.my_socket.accept()
                logging.warning(f"connection from {self.client_address}")
    
                clt = ProcessTheClient(self.connection, self.client_address)
                clt.start()
                self.the_clients.append(clt)
        except Exception as e:
            logging.error(f"Error happen when running server: {e}")
            self.my_socket.close()


def main():
    svr = Server(ipaddress='0.0.0.0',port=6677)
    svr.start()


if __name__ == "__main__":
    main()