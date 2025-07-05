import socket
import argparse
import os
import json
import logging

def send_request(request, is_binary=False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)  # Set timeout to prevent hanging
    try:
        sock.connect((args.host, args.port))
        sock.sendall(request)
        response = b""
        while True:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                response += data
            except socket.timeout:
                logging.warning(f"Timeout while receiving response from {args.host}:{args.port}")
                break
            except socket.error as e:
                logging.error(f"Socket error while receiving: {e}")
                break
        if is_binary:
            return response
        try:
            return response.decode('utf-8')
        except UnicodeDecodeError:
            logging.error("Failed to decode response as UTF-8, returning raw bytes")
            return response
    finally:
        try:
            sock.close()
            logging.info("Client socket closed")
        except socket.error as e:
            logging.error(f"Error closing socket: {e}")

def list_files():
    """Membuat dan mengirim request GET untuk daftar direktori."""
    request = f"GET / HTTP/1.1\r\nHost: {args.host}\r\n\r\n"
    print("--- Sending LIST request ---")
    response = send_request(request.encode())
    print("--- Server Response ---")
    print(response)

def upload_file(filepath):
    """Membaca file dan mengirimkannya via POST request ke /upload."""
    filename = os.path.basename(filepath)
    try:
        with open(filepath, 'rb') as f:
            content_bytes = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return

    headers = [
        f"POST /upload/{filename} HTTP/1.1",
        f"Host: {args.host}",
        f"Content-Length: {len(content_bytes)}",
        "Content-Type: application/octet-stream"
    ]
    header_text = "\r\n".join(headers) + "\r\n\r\n"

    request_bytes = header_text.encode('utf-8') + content_bytes
    
    print(f"--- Uploading {filepath} as {filename} ---")
    response = send_request(request_bytes, is_binary=True)
    print("--- Server Response ---")
    try:
        print(response.decode())
    except UnicodeDecodeError:
        print("Response contains binary data or is malformed.")

def delete_file(filename):
    """Membuat dan mengirim request DELETE ke /delete/{filename}."""
    request = f"DELETE /delete/{filename} HTTP/1.1\r\nHost: {args.host}\r\n\r\n"
    print(f"--- Deleting {filename} ---")
    response = send_request(request.encode())
    print("--- Server Response ---")
    print(response)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Simple HTTP Client")
    parser.add_argument('command', choices=['list', 'upload', 'delete'], help="Command to execute.")
    parser.add_argument('path', nargs='?', help="File path for upload or delete command.")
    parser.add_argument('--host', default='172.16.16.101', help="Server host.")
    parser.add_argument('--port', type=int, default=8885, help="Server port for thread pool, 8889 for process pool.")
    
    args = parser.parse_args()

    if args.command == 'list':
        list_files()
    elif args.command == 'upload':
        if not args.path:
            print("Error: 'upload' command requires a file path.")
        else:
            upload_file(args.path)
    elif args.command == 'delete':
        if not args.path:
            print("Error: 'delete' command requires a file name.")
        else:
            delete_file(os.path.basename(args.path))