from cgi import test
import requests
import os
import urllib.request

# function to test upload() method.

def upload(files):
  url = "http://127.0.0.1:5000/upload/test?apikey=xyz"

  payload={}
  # files=[
  #   ('files[]',('example.py',open(path,'rb'),'application/octet-stream'))
  # ]
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

# function to check build
def build(dir, graphml, apikey):
  url = "http://127.0.0.1:5000/build/"+dir+"?"+"fetch="+graphml+"&"+"apikey="+apikey
  response = requests.request("POST", url)
  print(response.text)

# function to debug
def debug(graphml):
  url = "http://127.0.0.1:5000/debug/"+graphml
  response = requests.request("POST", url)
  print(response.text) 


#function to destroy dir.
def destroy(dir):
  url = "http://127.0.0.1:5000/destroy/" + dir
  response = requests.request("DELETE", url)

  print(response.text)  
  
def getFilesList(dir):
  url = "http://127.0.0.1:5000/getFilesList/" + dir
  response = requests.request("POST", url)
  print(response.text) 

def openJupyter():
  url = "http://127.0.0.1:5000/openJupyter"
  response = requests.request("POST", url)
  print(response.text)

# function to test download() method.
def download():
  url = "http://127.0.0.1:5000/download/test?fetch=f1.txt&apikey=xyz"
  urllib.request.urlretrieve(url, "f1.txt")

# file list to be uploaded
files=[
  #('files[]',(file_name,open(file_path,'rb'),'application/octet-stream'))
  
]


upload(files)
execute()
build("test", "sample1", "xyz")
debug("sample1")
destroy("sample1")
# getFilesList("fri")
# openJupyter()
# download()

