from flask import Flask, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
from subprocess import call
from pathlib import Path
import json
import subprocess
from flask_cors import CORS, cross_origin

cur_path = os.path.dirname(os.path.abspath(__file__))
concore_path = os.path.abspath(os.path.join(cur_path, '../../'))


app = Flask(__name__)
app.secret_key = "secret key"

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# To upload multiple file. For example, /upload/test?apikey=xyz
@app.route('/upload/<dir>', methods=['POST'])
def upload(dir):
    apikey = request.args.get('apikey')
    dirname = secure_filename(dir) + "_" + apikey

    if 'files[]' not in request.files:
        resp = jsonify({'message': 'No file in the request'})
        resp.status_code = 400
        return resp

    files = request.files.getlist('files[]')

    errors = {}
    success = False

    directory_name = os.path.abspath(os.path.join(concore_path, secure_filename(dirname)))

    if not os.path.isdir(directory_name):
        os.mkdir(directory_name)


    for file in files:
        if file:
            filename = secure_filename(file.filename)
            file.save(directory_name+"/"+filename)
            success = True

    if success and errors:
        errors['message'] = 'File(s) successfully uploaded'
        resp = jsonify(errors)
        resp.status_code = 500
        return resp
    if success:
        resp = jsonify({'message': 'Files successfully uploaded'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify(errors)
        resp.status_code = 500
        return resp



# to download /build/<dir>?fetch=<graphml>. For example, /build/test?fetch=sample1&apikey=xyz
@app.route('/build/<dir>', methods=['POST'])
def build(dir):
    graphml_file = request.args.get('fetch')  
    apikey = request.args.get('apikey') 
    dirname = secure_filename(dir) + "_" + apikey   
    makestudy_dir = dirname + "/" + graphml_file   #for makestudy
    dir_path = os.path.abspath(os.path.join(concore_path, graphml_file)) #path for ./build
    if not os.path.exists(dir_path):
        proc = call(["makestudy", makestudy_dir],shell=True, cwd=concore_path)
        if(proc == 0):
            resp = jsonify({'message': 'Directory successfully created'})
            resp.status_code = 201
        else:
            resp = jsonify({'message': 'There is an Error'})
            resp.status_code = 500        
    else:
        resp= jsonify({"message":"Success"})
        resp.status_code=200
    call(["build"],shell=True, cwd=dir_path)   
    return resp 


@app.route('/debug/<dir>', methods=['POST'])
def debug(dir):
    dir = secure_filename(dir)
    dir_path = os.path.abspath(os.path.join(concore_path, dir))
    proc = call(["./debug"], cwd=dir_path)
    if(proc == 0):
        resp = jsonify({'message': 'Close the pop window after obtaining result'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'message': 'There is an Error'})
        resp.status_code = 500
        return resp  


@app.route('/run/<dir>', methods=['POST'])
def run(dir):
    dir = secure_filename(dir)
    dir_path = os.path.abspath(os.path.join(concore_path, dir))
    proc = call(["./run"], cwd=dir_path)
    if(proc == 0):
        resp = jsonify({'message': 'result prepared'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'message': 'There is an Error'})
        resp.status_code = 500
        return resp

@app.route('/stop/<dir>', methods=['POST'])
def stop(dir):
    dir = secure_filename(dir)
    dir_path = os.path.abspath(os.path.join(concore_path, dir))
    proc = call(["./stop"], cwd=dir_path)
    if(proc == 0):
        resp = jsonify({'message': 'resources cleaned'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'message': 'There is an Error'})
        resp.status_code = 500
        return resp                
                   

@app.route('/clear/<dir>', methods=['POST'])
def clear(dir):
    dir = secure_filename(dir)
    dir_path = os.path.abspath(os.path.join(concore_path, dir))
    proc = call(["./clear"], cwd=dir_path)
    if(proc == 0):
        resp = jsonify({'message': 'result deleted'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'message': 'There is an Error'})
        resp.status_code = 500
        return resp

# to download /download/<dir>?fetch=<downloadfile>. For example, /download/test?fetchDir=xyz&fetch=u
@app.route('/download/<dir>', methods=['POST', 'GET'])
def download(dir):
    download_file = request.args.get('fetch')
    sub_folder = request.args.get('fetchDir')
    dirname = secure_filename(dir) + "/" + secure_filename(sub_folder)
    directory_name = os.path.abspath(os.path.join(concore_path, dirname))
    if not os.path.exists(directory_name):
        resp = jsonify({'message': 'Directory not found'})
        resp.status_code = 400
        return resp
    try:
        return send_from_directory(directory_name, download_file, as_attachment=True)
    except:
        resp = jsonify({'message': 'file not found'})
        resp.status_code = 400
        return resp


@app.route('/destroy/<dir>', methods=['DELETE'])
def destroy(dir):
    dir = secure_filename(dir)
    proc = call(["./destroy", dir], cwd=concore_path)
    if(proc == 0):
        resp = jsonify({'message': 'Successfuly deleted Dirctory'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'message': 'There is an Error'})
        resp.status_code = 500
        return resp   

@app.route('/getFilesList/<dir>', methods=['POST'])
def getFilesList(dir):
    sub_dir = request.args.get('fetch')
    dirname = secure_filename(dir) + "/" + secure_filename(sub_dir)
    dir_path = os.path.abspath(os.path.join(concore_path, dirname))
    res = []
    res = os.listdir(dir_path) 
    res = json.dumps(res)  
    return res             


@app.route('/openJupyter/', methods=['POST'])
def openJupyter():
    proc = subprocess.Popen(['jupyter', 'lab'], shell=False, stdout=subprocess.PIPE, cwd=concore_path)
    if  proc.poll() is None:
        resp = jsonify({'message': 'Successfuly opened Jupyter'})
        resp.status_code = 308
        return resp
    else:
        resp = jsonify({'message': 'There is an Error'})
        resp.status_code = 500
        return resp 



if __name__ == "__main__":
    app.run(host="0.0.0.0")
