from flask import Flask, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
import xml.etree.ElementTree as ET
import os
import subprocess
from subprocess import call
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

def check_node_labels(graphml_file):
    tree = ET.parse(graphml_file)
    root = tree.getroot()
    namespace = {'y': 'http://www.yworks.com/xml/graphml'}
    node_labels = root.findall('.//y:NodeLabel', namespace)
    for node_label in node_labels:
        label = node_label.text
        if label.endswith('.m'):
            return True
    return False

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
    params = request.args.get('params')
    docker = request.args.get('docker')
    octave = request.args.get('octave')
    maxtime = request.args.get('maxtime')
    apikey = request.args.get('apikey') 
    out_dir = request.args.get('outdir')
    output_str = ""
    if(apikey == None):
        dirname = secure_filename(dir)
    else:
        dirname = secure_filename(dir) + "_" + apikey
    makestudy_dir = dirname + "/" + graphml_file   #for makestudy
    if(out_dir == None or out_dir == ""):
        dir_path = os.path.abspath(os.path.join(concore_path, graphml_file)) #path for ./build
    else:
        dir_path = os.path.abspath(os.path.join(concore_path, out_dir)) #path for ./build
    
    dotMCheck = check_node_labels(os.path.abspath(os.path.join(concore_path, makestudy_dir)) + '.graphml')
    if((dotMCheck == False or octave == 'false') and os.path.isfile(os.path.abspath(os.path.join(concore_path, 'concore.octave')))):
        if(platform.uname()[0]!='Windows'):
            proc= call(["rm", "concore.octave"], cwd=concore_path)
        else:
            proc= call(["del", "concore.octave"], shell=True, cwd=concore_path)

    if(octave == 'true' and dotMCheck):
        if(platform.uname()[0]!='Windows'):
            proc= call(["touch", "concore.octave"], cwd=concore_path)
        else:
            proc= open(os.path.abspath(os.path.join(concore_path, 'concore.octave')), 'x')
                        

    if not os.path.exists(dir_path):
        if(platform.uname()[0]=='Windows'):
            if(out_dir == None or out_dir == ""):
                if(docker == 'true'):
                    try:
                        output_bytes = subprocess.check_output(["makedocker", makestudy_dir], cwd=concore_path, shell=True)
                        output_str = output_bytes.decode("utf-8")
                        proc = 0
                    except subprocess.CalledProcessError as e:
                        output_str = f"Docker study creation failed with return code {e.returncode} (check duplicate directory)"
                        proc = 1
                else:
                    try:
                        output_bytes = subprocess.check_output(["makestudy", makestudy_dir], cwd=concore_path, shell=True)
                        output_str = output_bytes.decode("utf-8")
                        proc = 0
                    except subprocess.CalledProcessError as e:
                        output_str = f"Study creation failed with return code {e.returncode} (check duplicate directory)"
                        proc = 1
            else:
                if(docker == 'true'):
                    try:
                        output_bytes = subprocess.check_output(["makedocker", makestudy_dir, out_dir], cwd=concore_path, shell=True)
                        output_str = output_bytes.decode("utf-8")
                        proc = 0
                    except subprocess.CalledProcessError as e:
                        output_str = f"Docker study creation failed with return code {e.returncode} (check duplicate directory)"
                        proc = 1
                else:
                    try:
                        output_bytes = subprocess.check_output(["makestudy", makestudy_dir, out_dir], cwd=concore_path, shell=True)
                        output_str = output_bytes.decode("utf-8")
                        proc = 0
                    except subprocess.CalledProcessError as e:
                        output_str = f"Study creation failed with return code {e.returncode} (check duplicate directory)"
                        proc = 1
        else:
            if(out_dir == None or out_dir == ""):
                if(docker == 'true'):
                    try:
                        output_bytes = subprocess.check_output(["./makedocker", makestudy_dir], cwd=concore_path)
                        output_str = output_bytes.decode("utf-8")
                        proc = 0
                    except subprocess.CalledProcessError as e:
                        output_str = f"Docker study creation failed with return code {e.returncode} (check duplicate directory)"
                        proc = 1
                else:
                    try:
                        output_bytes = subprocess.check_output(["./makestudy", makestudy_dir], cwd=concore_path)
                        output_str = output_bytes.decode("utf-8")
                        proc = 0
                    except subprocess.CalledProcessError as e:
                        output_str = f"Study creation failed with return code {e.returncode} (check duplicate directory)"
                        proc = 1
            else:
                if(docker == 'true'):
                    try:
                        output_bytes = subprocess.check_output(["./makedocker", makestudy_dir, out_dir], cwd=concore_path)
                        output_str = output_bytes.decode("utf-8")
                        proc = 0
                    except subprocess.CalledProcessError as e:
                        output_str = f"Docker study creation failed with return code {e.returncode} (check duplicate directory)"
                        proc = 1
                else:
                    try:
                        output_bytes = subprocess.check_output(["./makestudy", makestudy_dir, out_dir], cwd=concore_path)
                        output_str = output_bytes.decode("utf-8")
                        proc = 0
                    except subprocess.CalledProcessError as e:
                        output_str = f"Study creation failed with return code {e.returncode} (check duplicate directory)"
                        proc = 1
        if(proc == 0):
            resp = jsonify({'message': 'Directory successfully created'})
            resp.status_code = 201
        else:
            resp = jsonify({'message': 'There is an Error'})
            resp.status_code = 500
    if(platform.uname()[0]=='Windows'):
        try:
            output_bytes = subprocess.check_output("build", cwd=dir_path, shell=True)
            output_str = output_str + output_bytes.decode("utf-8")
            resp = jsonify({'message': 'Directory successfully created', 'output': output_str})
        except subprocess.CalledProcessError as e:
            output_str = f"Build failed with return code {e.returncode}"
            resp = jsonify({'message': 'Build Failed', 'output': output_str})
            resp.status_code = 500
        if(maxtime != None and maxtime != ''):
            proc=call(["maxtime", maxtime],shell=True, cwd=dir_path)
        if(params != None and params != ''):
            proc=call(["params", params],shell=True, cwd=dir_path)
    else:
        try:
            output_bytes = subprocess.check_output("./build", cwd=dir_path)
            output_str = output_str + output_bytes.decode("utf-8")
            resp = jsonify({'message': 'Directory successfully created', 'output': output_str})
        except subprocess.CalledProcessError as e:
            output_str = f"Build failed with return code {e.returncode}"
            resp = jsonify({'message': 'Build Failed', 'output': output_str})
            resp.status_code = 500
        if(maxtime != None and maxtime != ''):
            proc=call(["./maxtime", maxtime], cwd=dir_path)
        if(params != None and params != ''):
            proc=call(["./params", params], cwd=dir_path)
    return resp 

@app.route('/debug/<dir>', methods=['POST'])
def debug(dir):
    dir_name = secure_filename(dir)
    dir_path = os.path.abspath(os.path.join(concore_path, dir_name))
    if(platform.uname()[0]=='Windows'):
        proc = call(["debug"],shell=True, cwd=dir_path)
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
        proc = call(["run"],shell=True, cwd=dir_path)
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
        proc = call(["stop"],shell=True, cwd=dir_path)
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
    unlock = request.args.get('unlock')
    params = request.args.get('params')
    maxtime = request.args.get('maxtime')
    dir_name = secure_filename(dir)
    dir_path = os.path.abspath(os.path.join(concore_path, dir_name))
    if(platform.uname()[0]=='Windows'):
        proc = call(["clear"],shell=True, cwd=dir_path)
        if(maxtime != None and maxtime != ''):
            proc = call(["maxtime", maxtime],shell=True, cwd=dir_path)
        if(params != None and params != ''):
            proc = call(["params", params],shell=True, cwd=dir_path)
    else:
        proc = call(["./clear"], cwd=dir_path)
        if(maxtime != None and maxtime != ''):
            proc = call(["./maxtime", maxtime], cwd=dir_path)
        if(params != None and params != ''):
            proc = call(["./params", params], cwd=dir_path)
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
    if(platform.uname()[0]=='Windows'):
        proc = call(["destroy", dir],shell=True, cwd=concore_path)
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
    
@app.route('/library/<dir>', methods=['POST'])
def library(dir):
    dir_name = secure_filename(dir)
    dir_path = os.path.abspath(os.path.join(concore_path, dir_name))
    filename = request.args.get('filename')
    library_path = request.args.get('path')
    proc = 0
    if (library_path == None or library_path  == ''):
        library_path = "../tools"
    if(platform.uname()[0]=='Windows'):
        proc = subprocess.check_output(["..\library", library_path, filename],shell=True, cwd=dir_path)
    else:
        proc = subprocess.check_output(["../library", library_path, filename], cwd=dir_path)
    if(proc != 0):
        resp = jsonify({'message': proc.decode("utf-8")})
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
