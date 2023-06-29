from flask import Flask, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
import subprocess
from subprocess import call,check_output
from pathlib import Path
import json
import platform
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
    if(apikey == None):
        dirname = secure_filename(dir)
    else:
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
    out_dir = request.args.get('outdir')
    if(apikey == None):
        dirname = secure_filename(dir)
    else:
        dirname = secure_filename(dir) + "_" + apikey
    makestudy_dir = dirname + "/" + graphml_file   #for makestudy
    if(out_dir == None or out_dir == ""):
        dir_path = os.path.abspath(os.path.join(concore_path, graphml_file)) #path for ./build
    else:
        dir_path = os.path.abspath(os.path.join(concore_path, out_dir)) #path for ./build
    if not os.path.exists(dir_path):
        if(platform.uname()[0]=='Windows'):
            if(out_dir == None or out_dir == ""):
                proc= call(["makestudy", makestudy_dir], shell=True, cwd=concore_path)
            else:
                proc= call(["makestudy", makestudy_dir, out_dir], shell=True, cwd=concore_path)
        else:
            if(out_dir == None or out_dir == ""):
                proc= call(["./makestudy", makestudy_dir], cwd=concore_path)
            else:
                proc= call(["./makestudy", makestudy_dir, out_dir], cwd=concore_path)
        if(proc == 0):
            resp = jsonify({'message': 'Directory successfully created'})
            resp.status_code = 201
        else:
            resp = jsonify({'message': 'There is an Error'})
            resp.status_code = 500   
    if(platform.uname()[0]=='Windows'):
        call(["build"], cwd=dir_path, shell=True)
    else:
        call(["./build"], cwd=dir_path)  
    return resp 

@app.route('/debug/<dir>', methods=['POST'])
def debug(dir):
    dir_name = secure_filename(dir)
    dir_path = os.path.abspath(os.path.join(concore_path, dir_name))
    if(platform.uname()[0]=='Windows'):
        proc=call(["debug"],shell=True, cwd=dir_path)
    else:
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
    dir_name = secure_filename(dir)
    dir_path = os.path.abspath(os.path.join(concore_path, dir_name))
    if(platform.uname()[0]=='Windows'):
        proc=call(["run"],shell=True, cwd=dir_path)
    else:
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
    dir_name = secure_filename(dir)
    dir_path = os.path.abspath(os.path.join(concore_path, dir_name))
    if(platform.uname()[0]=='Windows'):
        proc=call(["stop"],shell=True, cwd=dir_path)
    else:
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
    dir_name = secure_filename(dir)
    dir_path = os.path.abspath(os.path.join(concore_path, dir_name))
    if(platform.uname()[0]=='Windows'):
        proc=call(["clear"],shell=True, cwd=dir_path)
    else:
        proc = call(["./clear"], cwd=dir_path)
    if(proc == 0):
        resp = jsonify({'message': 'result deleted'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'message': 'There is an Error'})
        resp.status_code = 500
        return resp

@app.route('/contribute', methods=['POST'])
def contribute():
    try:
        data = request.json
        PR_TITLE = data.get('title')
        PR_BODY = data.get('desc')
        AUTHOR_NAME = data.get('auth')
        STUDY_NAME = data.get('study')
        STUDY_NAME_PATH = data.get('path')
        BRANCH_NAME = data.get('branch')
        if(platform.uname()[0]=='Windows'):
            proc=check_output(["contribute",STUDY_NAME,STUDY_NAME_PATH,AUTHOR_NAME,BRANCH_NAME,PR_TITLE,PR_BODY],cwd=concore_path,shell=True)
        else:
            if len(BRANCH_NAME)==0:
                proc = check_output(["./contribute",STUDY_NAME,STUDY_NAME_PATH,AUTHOR_NAME],cwd=concore_path)
            else:
                proc = check_output(["./contribute",STUDY_NAME,STUDY_NAME_PATH,AUTHOR_NAME,BRANCH_NAME,PR_TITLE,PR_BODY],cwd=concore_path)
        output_string = proc.decode()
        status=200
        if output_string.find("/pulls/")!=-1:
            status=200
        elif output_string.find("error")!=-1:
            status=501
        else:
            status=400
        return jsonify({'message': output_string}),status
    except Exception as e:
        output_string = "Some Error occured.Please try after some time"
        status=501
    return jsonify({'message': output_string}),status

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
    if(platform.uname()[0]=='Windows'):
        proc=call(["destroy", dir],shell=True, cwd=concore_path)
    else:
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
    app.run(host="0.0.0.0", port=5000)
