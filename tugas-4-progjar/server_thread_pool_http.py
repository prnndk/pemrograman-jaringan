from socket import *
import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from http import HttpServer

httpserver = HttpServer()

#untuk menggunakan threadpool executor, karena tidak mendukung subclassing pada process,
#maka class ProcessTheClient dirubah dulu menjadi function, tanpda memodifikasi behaviour didalamnya

def ProcessTheClient(connection, address):
    addr_str = f"[{address[0]}:{address[1]}]"
    
    try:
        headers = b""
        while b"\r\n\r\n" not in headers:
            try:
                chunk = connection.recv(1024)
                if not chunk:
                    logging.warning(f"{addr_str} Koneksi ditutup klien.")
                    break
                headers += chunk
            except socket.timeout:
                logging.warning(f"{addr_str}. Timeout membaca headers.")
                break
        

        if b"\r\n\r\n" not in headers:
            logging.error(f"{addr_str} Headers tidak lengkap. Menutup koneksi.")
            connection.close()
            return

        header_bytes, body_start = headers.split(b'\r\n\r\n', 1)
        header_str = header_bytes.decode('utf-8')

        content_length = 0
        for line in header_str.split('\r\n'):
            if line.lower().startswith('content-length:'):
                try:
                    content_length = int(line.split(':', 1)[1].strip())
                except (ValueError, IndexError):
                    content_length = 0
                break

        body = body_start
        
        while len(body) < content_length:
            try:
                bytes_to_read = min(4096, content_length - len(body))
                chunk = connection.recv(bytes_to_read)
                if not chunk:
                    logging.warning(f"{addr_str} Koneksi ditutup klien.")
                    break
                body += chunk
            except socket.timeout:
                logging.warning(f"{addr_str} Terjadi Timeout saat membaca body.")
                break
        full_request = header_bytes + b'\r\n\r\n' + body
        
        hasil = httpserver.proses(full_request)
        
        connection.sendall(hasil)
    except Exception as e:
        logging.error(f"{addr_str} >> Terjadi error tak terduga: {e}", exc_info=True)
    finally:
        logging.warning(f"{addr_str} >> Menutup koneksi.")
        connection.close()


def Server():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.bind(('0.0.0.0', 8885))
    my_socket.listen(5)
    logging.warning("Thread Pool Server running on port 8885")

    with ThreadPoolExecutor(20) as executor:
        while True:
            connection, client_address = my_socket.accept()
            connection.settimeout(2.0) 
            logging.warning(f"Connection from {client_address}")
            executor.submit(ProcessTheClient, connection, client_address)

def main():
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
    Server()

if __name__ == "__main__":
    main()