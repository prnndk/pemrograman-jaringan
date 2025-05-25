from socket import *
import socket
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from file_protocol import FileProtocol

fp = FileProtocol()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [SERVER] - %(levelname)s - %(message)s')

def ProcessTheClient(connection, address):
    command_buffer = ""
    total_bytes_processed = 0
    successful_operations = 0
    failed_operations = 0
    start_time_client_process = time.time()

    logging.info(f"Connected by {address}")
    try:
        while True:
            try:
                data = connection.recv(1024*1024)
                if not data:
                    logging.info(f"Client {address} disconnected.")
                    break

                total_bytes_processed += len(data)

                try:
                    d = data.decode()
                except UnicodeDecodeError as e:
                    logging.error(f"Decode error from {address}: {e}")
                    failed_operations += 1
                    break

                command_buffer += d

                while "\r\n\r\n" in command_buffer:
                    complete_command, _, command_buffer = command_buffer.partition("\r\n\r\n")
                    
                    hasil = fp.proses_string(complete_command.strip())
                    hasil += "\r\n\r\n"

                    connection.sendall(hasil.encode())
                    total_bytes_processed += len(hasil.encode())
                    successful_operations += 1

            except OSError as e:
                logging.warning(f"OSError with client {address}: {e}")
                failed_operations += 1
                break
            except Exception as e:
                logging.error(f"Unexpected error with client {address}: {e}")
                failed_operations += 1
                break
    finally:
        connection.close()
        end_time_client_process = time.time()
        duration = end_time_client_process - start_time_client_process
        throughput = (total_bytes_processed / duration) if duration > 0 else 0
        logging.info(f"Client {address} session finished. "
                     f"Time: {duration:.2f}s, "
                     f"Throughput: {throughput:.2f} bytes/s, "
                     f"Successful ops: {successful_operations}, "
                     f"Failed ops: {failed_operations}")

        Server.server_successful_workers += successful_operations
        Server.server_failed_workers += failed_operations
        Server.server_total_bytes_processed += total_bytes_processed
        Server.server_total_client_process_time += duration


class Server:
    server_successful_workers = 0
    server_failed_workers = 0
    server_total_bytes_processed = 0
    server_total_client_process_time = 0
    
    def __init__(self, server_address=('0.0.0.0', 6677), num_server_workers=5):
        self.server_address = server_address
        self.num_server_workers = num_server_workers
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        logging.info(f"Server starting on: {self.server_address}")
        logging.info(f"Server worker pool size: {self.num_server_workers}")
        self.my_socket.bind(self.server_address)
        self.my_socket.listen(50)

        with ThreadPoolExecutor(max_workers=self.num_server_workers) as executor:
            while True:
                connection, client_address = self.my_socket.accept()
                p = executor.submit(ProcessTheClient, connection, client_address)
                self.the_clients.append(p)
                self.the_clients = [future for future in self.the_clients if not future.done()]
                logging.info(f"Active server workers: {len([f for f in self.the_clients if f.running()])}")

    def shutdown(self):
        logging.info("Shutting down server...")
        self.my_socket.close()
        logging.info(f"Total server successful operations: {Server.server_successful_workers}")
        logging.info(f"Total server failed operations: {Server.server_failed_workers}")
        logging.info(f"Total bytes processed by server: {Server.server_total_bytes_processed}")
        logging.info(f"Total client processing time on server: {Server.server_total_client_process_time:.2f}s")


def main():
    num_server_workers = 50 # Ganti value ini sesuai dengan spesifikasi tugas
    server = Server(num_server_workers=num_server_workers)
    try:
        server.start()
    except KeyboardInterrupt:
        server.shutdown()
    except Exception as e:
        logging.critical(f"Server error: {e}")
        server.shutdown()

if __name__ == "__main__":
    main()