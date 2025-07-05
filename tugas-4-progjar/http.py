import sys
import os.path
import uuid
import json
from glob import glob
from datetime import datetime

class HttpServer:
	
	def __init__(self):
		self.sessions={}
		self.types={}
		self.types['.pdf']='application/pdf'
		self.types['.jpg']='image/jpeg'
		self.types['.txt']='text/plain'
		self.types['.html']='text/html'
		self.files_directory = './'
		self.types['.html']='text/html'
	def response(self,kode=404,message='Not Found',messagebody=bytes(),headers={}):
		tanggal = datetime.now().strftime('%c')
		resp=[]
		resp.append("HTTP/1.0 {} {}\r\n" . format(kode,message))
		resp.append("Date: {}\r\n" . format(tanggal))
		resp.append("Connection: close\r\n")
		resp.append("Server: myserver/1.0\r\n")
		resp.append("Content-Length: {}\r\n" . format(len(messagebody)))
		for kk in headers:
			resp.append("{}:{}\r\n" . format(kk,headers[kk]))
		resp.append("\r\n")

		response_headers=''
		for i in resp:
			response_headers="{}{}" . format(response_headers,i)
		#menggabungkan resp menjadi satu string dan menggabungkan dengan messagebody yang berupa bytes
		#response harus berupa bytes
		#message body harus diubah dulu menjadi bytes
		if (type(messagebody) is not bytes):
			messagebody = messagebody.encode()

		response = response_headers.encode() + messagebody
		#response adalah bytes
		return response

	def proses(self,data):
		heaader_bytes, body_bytes = data.split(b'\r\n\r\n', 1)
		header_text = heaader_bytes.decode('utf-8')
		
		requests = header_text.split("\r\n")
		#print(requests)

		baris = requests[0]
		#print(baris)

		all_headers = [n for n in requests[1:] if n!='']

		j = baris.split(" ")
		try:
			method=j[0].upper().strip()
			if (method=='GET'):
				object_address = j[1].strip()
				return self.http_get(object_address, all_headers)
			if (method=='POST'):
				object_address = j[1].strip()
				return self.http_post(object_address, all_headers, body_bytes)
			if (method=='DELETE'):
				object_address = j[1].strip()
				return self.http_delete(object_address, all_headers)
			else:
				return self.response(400,'Bad Request','',{})
		except IndexError:
			return self.response(400,'Bad Request','',{})
	def http_get(self,object_address,headers):
		if object_address == '/':
			return self.process_list_directory(self.files_directory)
		file_path = os.path.join(self.files_directory, object_address.lstrip('/'))
		if not os.path.exists(file_path):
			return self.response(404, 'Not Found', '{"error": "File not found"}')
		if os.path.exists(file_path) and os.path.isfile(file_path):
			with open(file_path, 'rb') as f:
				file_data = f.read()
			file_extension = os.path.splitext(file_path)[1].lower()
			content_type = self.types.get(file_extension, 'application/octet-stream')
			headers = {'Content-Type': content_type}
			return self.response(200, 'OK', file_data, headers)
		elif os.path.isdir(file_path):
			return self.process_list_directory(object_address)

	def http_post(self, object_address, headers, body_bytes=None):
		if object_address.startswith('/upload'):
			if body_bytes is None:
				return self.response(400, 'Bad Request', 'No file data provided.')
			
			parts = object_address.split('/')
			if len(parts) > 2:
				filename = parts[-1]
			else:
				filename = None
				for header in headers:
					if header.startswith('Filename:'):
						filename = header.split(':', 1)[1].strip()
						break
				
				if not filename:
					return self.response(400, 'Bad Request', 'Filename not provided in path or headers.')
					
			return self.process_file_upload(body_bytes, filename)
		else:
			return self.response(404, 'Not Found', '{"error": "Endpoint not found"}')
	def http_delete(self, object_address, headers):
		if object_address.startswith('/delete/'):
			filename = object_address.split('/')[-1]
			return self.process_delete_file(filename)
		else:
			return self.response(404, 'Not Found', '{"error": "Endpoint not found"}')
	def process_list_directory(self, directory):
		safe_directory_part = directory.lstrip('/')
		safe_path = os.path.abspath(os.path.join(self.files_directory, safe_directory_part))

		if not safe_path.startswith(os.path.abspath(self.files_directory)):
			return self.response(403, "Forbidden", "Access denied.")

		if os.path.exists(safe_path) and os.path.isdir(safe_path):
			try:
				file_list = os.listdir(safe_path)
				files_json = json.dumps(file_list)
				
				headers = {'Content-Type': 'application/json'}
				return self.response(200, 'OK', files_json, headers)
			except Exception as e:
				return self.response(500, 'Internal Server Error', f'{{"error": "{e}"}}')
		else:
			return self.response(404, 'Not Found', '{"error": "Directory not found"}')
		
	def process_file_upload(self, file_data, filename):
		if not filename:
			return self.response(400, 'Bad Request', 'Filename is required.')
			
		file_path = os.path.join(self.files_directory, filename)
		try:
			with open(file_path, 'wb') as f:
				f.write(file_data)
			return self.response(201, 'Created', f'File {filename} uploaded successfully.')
		except Exception as e:
			return self.response(500, 'Internal Server Error', f'{{"error": "{e}"}}')
		
	def process_delete_file(self, filename):
		file_path = os.path.join(self.files_directory, filename)
		if not os.path.exists(file_path):
			return self.response(404, 'Not Found', f'File {filename} does not exist.')
		
		try:
			os.remove(file_path)
			return self.response(200, 'OK', f'File {filename} deleted successfully.')
		except Exception as e:
			return self.response(500, 'Internal Server Error', f'{{"error": "{e}"}}')

		
			 	
#>>> import os.path
#>>> ext = os.path.splitext('/ak/52.png')

if __name__=="__main__":
	httpserver = HttpServer()