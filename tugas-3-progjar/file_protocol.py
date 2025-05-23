import json
import logging
import shlex

from file_interface import FileInterface

"""
* class FileProtocol bertugas untuk memproses 
data yang masuk, dan menerjemahkannya apakah sesuai dengan
protokol/aturan yang dibuat

* data yang masuk dari client adalah dalam bentuk bytes yang 
pada akhirnya akan diproses dalam bentuk string

* class FileProtocol akan memproses data yang masuk dalam bentuk
string
"""

class FileProtocol:
    def __init__(self):
        self.file = FileInterface()
    def proses_string(self,string_datamasuk=''):
        c = shlex.split(string_datamasuk)
        parts = shlex.split(string_datamasuk)
        if len(parts) >= 3:
            c = [parts[0].lower(), parts[1].lower()] + [parts[2]] + parts[3:]
        elif len(parts) == 2:
            c = [parts[0].lower(), parts[1].lower()]
        elif len(parts) == 1:
            c = [parts[0].lower()]
        else:
            c = parts
        try:
            c_request = c[0].strip()
            logging.warning(f"memproses request: {c_request}")
            params = [x for x in c[1:]]
            cl = getattr(self.file,c_request)(params)
            return json.dumps(cl)
        except Exception as e:
            return json.dumps({"status": "ERROR", "data": f"Request tidak dikenali: {str(e)}"})


if __name__=='__main__':
    #contoh pemakaian
    fp = FileProtocol()
    print(fp.proses_string("LIST"))
    print(fp.proses_string("GET pokijan.jpg"))
