import requests
import os

url = "http://127.0.0.1:5000/multiple-files-upload"

path = os.path.abspath("example.py")

payload={}
files=[
  ('files[]',('example.py',open( path,'rb'),'application/octet-stream'))
]
headers = {}

response = requests.request("POST", url, headers=headers, data=payload, files=files)

print(response.text)
