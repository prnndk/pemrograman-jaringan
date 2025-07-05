import socket
import logging
from concurrent.futures import ProcessPoolExecutor
from http import HttpServer

httpserver = HttpServer()

def handle_client_connection(sock, client_addr):
    addr_info = f"[{client_addr[0]}:{client_addr[1]}]"
    try:

        header_data = b""
        while b"\r\n\r\n" not in header_data:
            try:
                chunk = sock.recv(2048)
                if not chunk:
                    logging.warning(f"{addr_info} Client menutup koneksi.")
                    return
                header_data += chunk
            except socket.timeout:
                logging.warning(f"{addr_info} Timeout saat membaca header.")
                sock.close()
                return

        if b"\r\n\r\n" not in header_data:
            logging.error(f"{addr_info} Invalid header. Menutup koneksi.")
            sock.close()
            return

        header_bytes, initial_body = header_data.split(b'\r\n\r\n', 1)
        header_text = header_bytes.decode('utf-8')

        body_length = 0
        for line in header_text.split('\r\n'):
            if line.lower().startswith('content-length:'):
                try:
                    body_length = int(line.split(':', 1)[1].strip())
                except (ValueError, IndexError):
                    body_length = 0
                break

        body_data = initial_body
        while len(body_data) < body_length:
            try:
                remaining_bytes = body_length - len(body_data)
                chunk = sock.recv(min(2048, remaining_bytes))
                if not chunk:
                    return
                body_data += chunk
            except socket.timeout:
                logging.warning(f"{addr_info} Timeout saat membaca body.")
                return

        full_request = header_bytes + b'\r\n\r\n' + body_data

        response = httpserver.proses(full_request)

        sock.sendall(response)
        logging.info(f"{addr_info} Respons berhasil dikirim.")

    except Exception as e:
        logging.error(f"{addr_info} Kesalahan tidak terduga: {e}", exc_info=True)
    finally:
        logging.info(f"{addr_info} Menutup koneksi dengan klien.")
        sock.close()

def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 8889))
    server_socket.listen(5)
    logging.info("Server berjalan pada port 8889 dengan ProcessPoolExecutor")

    with ProcessPoolExecutor(max_workers=20) as executor:
        while True:
            client_sock, client_addr = server_socket.accept()
            client_sock.settimeout(2.0)
            logging.info(f"Koneksi baru dari {client_addr}")
            executor.submit(handle_client_connection, client_sock, client_addr)

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    run_server()

if __name__ == "__main__":
    main()