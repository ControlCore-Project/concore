#This file is just to check if friApi.py works perfectly.
import requests

url = "http://127.0.0.1:5000/upload_files"

payload={}
# replace as example.py with target file name and it must already exist in given Dir.
files=[
    ('files[]',('example.py',open('/Users/ASUS/concore/fri/example.py','rb'),'application/octet-stream')),
    ]
headers = {}

response = requests.request("POST", url, headers=headers, data=payload, files=files)

print(response.text)
