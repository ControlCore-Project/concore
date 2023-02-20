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
def debug(graphml, apikey):
  url = "http://127.0.0.1:5000/debug/"+graphml+"?"+"apikey="+apikey
  response = requests.request("POST", url)
  print(response.text) 

# function to test run() method.
def run(graphml, apikey):
  url = "http://127.0.0.1:5000/run/"+graphml+"?"+"apikey="+apikey
  response = requests.request("POST", url)
  print(response.text)

def clear(graphml, apikey):
  url = "http://127.0.0.1:5000/clear/"+graphml+"?"+"apikey="+apikey
  response = requests.request("POST", url)
  print(response.text)

def stop(graphml, apikey):
  url = "http://127.0.0.1:5000/stop/"+graphml+"?"+"apikey="+apikey
  response = requests.request("POST", url)
  print(response.text)    


#function to destroy dir.
def destroy(dir, apikey):
  url = "http://127.0.0.1:5000/destroy/" + dir+"?"+"apikey="+apikey
  response = requests.request("DELETE", url)

  print(response.text)  
  
def getFilesList(apikey, dir, sub_dir = ""):
  url = "http://127.0.0.1:5000/getFilesList/" + dir + "?"+"fetch="+sub_dir+"&"+"apikey="+apikey
  response = requests.request("POST", url)
  print(response.text) 

def openJupyter():
  url = "http://127.0.0.1:5000/openJupyter"
  response = requests.request("POST", url)
  print(response.text)

# function to test download() method.
def download(dir, subDir, fileName , apikey ):
  url = "http://127.0.0.1:5000/download/"+dir+"?"+"fetchDir="+subDir+"&"+"fetch="+ fileName+"&"+"apikey="+apikey
  urllib.request.urlretrieve(url, fileName)

# file list to be uploaded
cur_path = os.path.dirname(os.path.abspath(__file__))
demo_path = os.path.abspath(os.path.join(cur_path, '../demo'))
file_name1 = "controller.py"
file_name2 = "pm.py"
file_name3 = "sample.graphml"
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
build("test", "sample", "xyz")
time.sleep(6)
method = input("methods - 1 for debug, 0 for run :")
if method == "1":
  debug("sample", "xyz")
else:  
  run("sample", "xyz")
time.sleep(2)  
stop("sample", "xyz")
time.sleep(2) 
getFilesList("xyz", "sample", "CU")
getFilesList("xyz","sample", "PYM") 
time.sleep(5)
download("sample", "CU", "U", "xyz")
clear("sample", "xyz")
destroy("sample", "xyz")
openJupyter()


