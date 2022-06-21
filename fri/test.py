import requests

url = "http://127.0.0.1:5000/multiple-files-upload"

payload={}
files=[
  ('files[]',('example.py',open('/home/amit/Desktop/concore/flaskApi/example.py','rb'),'application/octet-stream'))
]
headers = {}

response = requests.request("POST", url, headers=headers, data=payload, files=files)

print(response.text)
