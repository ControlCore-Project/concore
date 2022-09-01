from cgi import test
import requests
import os
import urllib.request
import time

# function to test upload() method.

def upload(files):
  url = "http://127.0.0.1:5000/upload/test?apikey=xyz"
  payload={}
  headers = {}
  response = requests.request("POST", url, headers=headers, data=payload, files=files)
  print(response.text)


# # *******

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

# function to test run() method.
def run(graphml):
  url = "http://127.0.0.1:5000/run/"+graphml
  response = requests.request("POST", url)
  print(response.text)

def clear(graphml):
  url = "http://127.0.0.1:5000/clear/"+graphml
  response = requests.request("POST", url)
  print(response.text)

def stop(graphml):
  url = "http://127.0.0.1:5000/stop/"+graphml
  response = requests.request("POST", url)
  print(response.text)    


#function to destroy dir.
def destroy(dir):
  url = "http://127.0.0.1:5000/destroy/" + dir
  response = requests.request("DELETE", url)

  print(response.text)  
  
def getFilesList(dir, sub_dir = ""):
  url = "http://127.0.0.1:5000/getFilesList/" + dir + "?"+"fetch="+sub_dir
  response = requests.request("POST", url)
  print(response.text) 

def openJupyter():
  url = "http://127.0.0.1:5000/openJupyter"
  response = requests.request("POST", url)
  print(response.text)

# function to test download() method.
def download(dir, subDir, fileName ):
  url = "http://127.0.0.1:5000/download/"+dir+"?"+"fetchDir="+subDir+"&"+"fetch="+ fileName
  urllib.request.urlretrieve(url, fileName)

# file list to be uploaded
cur_path = os.path.dirname(os.path.abspath(__file__))
demo_path = os.path.abspath(os.path.join(cur_path, '../demo'))
file_name1 = "controller.py"
file_name2 = "pm.py"
file_name3 = "sample1.graphml"
path_file1 = demo_path + "/" +file_name1
path_file2 = demo_path + "/" +file_name2
path_file3 = demo_path + "/" +file_name3
files=[
  #('files[]',(file_name,open(file_path,'rb'),'application/octet-stream'))
  ('files[]',(file_name1,open(path_file1,'rb'),'application/octet-stream')),
  ('files[]',(file_name2,open(path_file2,'rb'),'application/octet-stream')),
  ('files[]',(file_name3,open(path_file3,'rb'),'application/octet-stream')),
]


upload(files)
time.sleep(2)
build("test", "sample1", "xyz")
time.sleep(6)
method = input("methods - 1 for debug, 0 for run :")
if method == 1:
  debug("sample1")
else:  
  run("sample1")
time.sleep(2)  
stop("sample1")
time.sleep(2) 
getFilesList("sample1", "cu")
getFilesList("sample1", "pym") 
time.sleep(5)
download("sample1", "cu", "u")
clear("sample1")
destroy("sample1")
openJupyter()


