import os
import base64
from glob import glob

class FileInterface:
    def __init__(self):
        # Handling multiprocessing errors with file paths
        script_dir = os.path.dirname(os.path.abspath(__file__))

        self.base_files_dir = os.path.join(script_dir, 'files')

        if not os.path.exists(self.base_files_dir):
            os.makedirs(self.base_files_dir)
        

    def list(self,params=[]):
        try:
            filelist = glob('*.*')
            return dict(status='OK',data=filelist)
        except Exception as e:
            return dict(status='ERROR',data=str(e))

    def get(self,params=[]):
        try:
            filename = params[0]
            if (filename == ''):
                return None
            fp = open(f"{filename}",'rb')
            isifile = base64.b64encode(fp.read()).decode()
            return dict(status='OK',data_namafile=filename,data_file=isifile)
        except Exception as e:
            return dict(status='ERROR',data=str(e))
    
    def upload(self,fileReq=[]):
        try:
            filename, fileContent = fileReq
            data = base64.b64decode(fileContent)
            with open(filename, 'wb') as f:
                f.write(data)
            return dict(status='OK',data='File uploaded successfully')
        except Exception as e:
            return dict(status='ERROR',data=str(e))

    def delete(self, fileReq=[]):
        try:
            filename = fileReq[0]
            if not os.path.exists(filename):
                return dict(status='ERROR',data='File not found')
            os.remove(filename)
            return dict(status='OK',data='File deleted successfully')
        except Exception as e:
            return dict(status='ERROR',data=str(e))


if __name__=='__main__':
    f = FileInterface()
    print(f.list())
    print(f.get(['pokijan.jpg']))
