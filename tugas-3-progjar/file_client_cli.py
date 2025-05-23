import socket
import json
import base64
import logging
import os

server_address=('0.0.0.0',7777)

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.info(f"connecting to {server_address}")
    try:
        command_str = command_str + "\r\n\r\n"
        sock.sendall(command_str.encode())
        # Look for the response, waiting until socket is done (no more data)
        data_received=""
        while True:
            data = sock.recv(1024)
            if data:
                data_received += data.decode()
                # Log chunks received by client for debugging
                logging.debug(f"Client received chunk: {repr(data.decode())}")
                if "\r\n\r\n" in data_received:
                    logging.debug("Client detected end of server message.")
                    break
            else:
                logging.warning("Client: No more data from server (socket closed by peer?).")
                break
        
        if data_received:
            json_part, _, _ = data_received.partition("\r\n\r\n")
            cleaned_data = json_part.strip()
        else:
            cleaned_data = ""
            
        logging.debug(f"Client raw data received from server (before JSON parse): {repr(cleaned_data)}")
        
        if not cleaned_data:
            logging.error("Client received no parsable data from server.")
            return {'status': 'ERROR', 'data': 'No data received from server'}

        hasil = json.loads(cleaned_data)
        return hasil
    except Exception as e:
        logging.warning("error during data receiving")
        return {'status':'ERROR', 'data': str(e)}
    finally:
        sock.close()


def remote_list():
    command_str=f"LIST"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        print("daftar file : ")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal")
        return False

def remote_get(filename=""):
    if not filename:
        print("Error: Filename is required")
        return False
    command_str = f"GET {filename}"
    hasil = send_command(command_str)
    if hasil.get('status') == 'OK':
        try:
            namafile = hasil['data_namafile']
            isifile = base64.b64decode(hasil['data_file'])
            with open(namafile, 'wb') as fp:
                fp.write(isifile)
            print(f"File {namafile} successfully downloaded")
            return True
        except KeyError as e:
            print(f"Error: Missing expected field in response: {e}")
            return False
        except base64.binascii.Error as e:
            print(f"Error: Invalid base64 content: {e}")
            return False
        except Exception as e:
            print(f"Error writing file: {e}")
            return False
    else:
        print(f"Operasi Get Gagal: {hasil}")
        return False

def remote_upload(filename=""):
    if not os.path.isfile(filename):
        print(f"File {filename} tidak ada")
        return False
    fn = os.path.basename(filename)
    with open(filename,'rb') as fp:
        encoded_file =  base64.b64encode(fp.read()).decode()
    result = send_command(f"UPLOAD {fn} {encoded_file}")
    if result.get('status') == 'OK':
        print(f"File {filename} berhasil diupload")
        return True
    else:
        print(f"File {filename} gagal diupload")
        return False

def remote_delete(filename=""):
    hasil = send_command(f"DELETE {filename}")
    
    if (hasil['status']=='OK'):
        print(f"File {filename} berhasil dihapus")
        return True
    else:
        print(f"File {filename} gagal dihapus")
        return False

def command_list():
    print("Daftar perintah yang bisa digunakan:")
    print("1. LIST")
    print("2. GET <filename>")
    print("3. UPLOAD <filename>")
    print("4. DELETE <filename>")
    print("5. EXIT")
    print("6. HELP")
    print("7. CLEAR")

def command_handler(command):
    if command.startswith("LIST"):
        remote_list()
    elif command.startswith("GET"):
        parts = command.split(maxsplit=1)
        if len(parts) > 1:
            filename = parts[1]
            remote_get(filename)
        else:
            print("GET membutuhkan nama file")
    elif command.startswith("UPLOAD"):
        parts = command.split(maxsplit=1)
        if len(parts) > 1:
            filename = parts[1]
            remote_upload(filename)
        else:
            print("UPLOAD membutuhkan nama file")
    elif command.startswith("DELETE"):
        parts = command.split(maxsplit=1)
        if len(parts) > 1:
            filename = parts[1]
            remote_delete(filename)
        else:
            print("DELETE membutuhkan nama file")
    elif command.startswith("EXIT"):
        print("Exiting...")
        exit(0)
    elif command.startswith("HELP"):
        command_list()
    elif command.startswith("CLEAR"):
        os.system('cls' if os.name == 'nt' else 'clear')
    else:
        print("Perintah tidak dikenali, ketik HELP untuk daftar perintah yang bisa digunakan")

if __name__=='__main__':
    server_address=('172.16.16.101',6677)
    command_list()
    while True:
        command = input("Masukkan perintah: ")
        command_handler(command)