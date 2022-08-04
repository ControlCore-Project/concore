import requests
import os
import urllib.request

# function to test upload() method.
def upload():
  url = "http://127.0.0.1:5000/upload/test?apikey=xyz"

  path = os.path.abspath("example.py")

  payload={}
  files=[
    ('files[]',('example.py',open(path,'rb'),'application/octet-stream'))
  ]
  headers = {}

  response = requests.request("POST", url, headers=headers, data=payload, files=files)

  print(response.text)


# # *******

# function to test execute() method.
def execute():
  url = "http://127.0.0.1:5000/execute/test?apikey=xyz"

  path = os.path.abspath("example.py")

  payload={}
  files=[
    ('file',('example.py',open(path,'rb'),'application/octet-stream'))
  ]
  headers = {}

  response = requests.request("POST", url, headers=headers, data=payload, files=files)

  print(response.text)

# function to test download() method.
def download():
  url = "http://127.0.0.1:5000/download/test?fetch=f1.txt&apikey=xyz"
  urllib.request.urlretrieve(url, "f1.txt")


# function to check build
def build():
  url = "http://127.0.0.1:5000/build/test?fetch=sample1"
  response = requests.request("POST", url)
  print(response.text)

# function to debug
def debug():
  url = "http://127.0.0.1:5000/debug/sample1"
  response = requests.request("POST", url)
  print(response.text) 


#function to destroy dir.
def destroy():
  url = "http://127.0.0.1:5000/destroy/sample1"
  response = requests.request("DELETE", url)

  print(response.text)  
  
def getFilesList():
  url = "http://127.0.0.1:5000/getFilesList/test"
  response = requests.request("POST", url)
  print(response.text) 

def openJupyterLa():
  url = "http://127.0.0.1:5000/openJupyterLab"
  response = requests.request("POST", url)
  print(response.text)


# upload()
# execute()
# download()
# build()
# debug()
# destroy()
getFilesList()
# openJupyterLa()

