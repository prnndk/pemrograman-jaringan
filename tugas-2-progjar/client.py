import socket
import logging
import sys


def initialize_socket(server_address):
    connect_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logging.warning(f"Membuka koneksi socket dengan: {server_address}")

    connect_sock.connect(server_address)

    return connect_sock


def close_socket(sock):
    logging.warning(f"Menutup koneksi socket dengan: {sock.getsockname()}")
    sock.close()


def send_message_to_server(message, sock):
    message_decoded = (message + '\r\n').encode()

    data_received = ''
    try:
        sock.sendall(message_decoded)
        amount_received = 0
        amount_expected = len(message_decoded)
        if message == 'QUIT':
            return None
        while amount_received < amount_expected:
            data = sock.recv(32)
            amount_received += len(data)
            if data:
                data_received += data.decode()
                if "\r\n" in data_received:
                    data_received = data_received.strip('\r\n')
                    break


    except (ConnectionError, ConnectionResetError, BrokenPipeError, socket.error) as e:
        logging.warning(f"[CLIENT] error sending message to server: {e}")
        close_socket(sock)

    return sock, data_received


if __name__ == '__main__':
    sock = None
    try:
        sock = initialize_socket(("localhost", 45000))
        while True:
            message = input("Sent your message to server: {TIME/QUIT} ")

            result = send_message_to_server(message, sock)

            if message == "QUIT":
                break

            if isinstance(result, tuple):
                sock, success = result
                if sock is None:
                    sys.exit(0)

                print(f"[RESPONSE SERVER]: {success}")
            else:
                break
    except KeyboardInterrupt:
        logging.warning("Received keyboard interrupt")
        close_socket(sock)
    finally:
        close_socket(sock)
