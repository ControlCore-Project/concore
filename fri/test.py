import requests
import os

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

  return response.text


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

  return response.text

  # ********
  # To Download call the url .../download/test?fetch=<filename>&apikey=xyz 

upload()
execute()

