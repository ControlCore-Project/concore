from flask import Flask, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
from subprocess import call
from pathlib import Path


app = Flask(__name__)
app.secret_key = "secret key"

# To upload multiple file. For example, /upload/test?apikey=xyz
@app.route('/upload/<dir>', methods=['POST'])
def upload(dir):
    apikey = request.args.get('apikey')
    dirname = dir + "_" + apikey

    if 'files[]' not in request.files:
        resp = jsonify({'message': 'No file in the request'})
        resp.status_code = 400
        return resp

    files = request.files.getlist('files[]')

    errors = {}
    success = False

    if not os.path.exists(secure_filename(dirname)):
        os.makedirs(secure_filename(dirname))

    for file in files:
        if file:
            filename = secure_filename(file.filename)
            file.save(secure_filename(dirname)+"/"+filename)
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

# To execute any python file. For example, /execute/test?apikey=xyz
@app.route('/execute/<dir>', methods=['POST'])
def execute(dir):
    apikey = request.args.get('apikey')
    dirname = dir + "_" + apikey

    if 'file' not in request.files:
        resp = jsonify({'message': 'No file in the request'})
        resp.status_code = 400
        return resp

    file = request.files['file']

    if file.filename == '':
        resp = jsonify({'message': 'No file selected for Executing'})
        resp.status_code = 400
        return resp

    errors = {}
    success = False

    if not os.path.exists(secure_filename(dirname)):
        os.makedirs(secure_filename(dirname))

    if file:
        filename = secure_filename(file.filename)
        file.save(secure_filename(dirname)+"/"+filename)
        output_filename = filename + ".out"
        file_path = secure_filename(dirname) + "/"+filename
        outputfile_path = secure_filename(dirname)+"/"+output_filename
        f = open(outputfile_path, "w")
        call(["nohup", "python3", file_path], stdout=f)
        success = True

    if success:
        resp = jsonify({'message': 'Files successfully executed'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify(errors)
        resp.status_code = 500
        return resp

# to download /build/<dir>?fetch=<graphml>. For example, /build/test?fetch=sample1
@app.route('/build/<dir>', methods=['POST'])
def build(dir):
    graphml_file = request.args.get('fetch')      
    makestudy_dir = dir+ "/" + graphml_file   #for makestudy
    cur_path = os.getcwd()
    concore_path = os.path.abspath(os.path.join(cur_path, '../../'))
    dir_path = os.path.abspath(os.path.join(concore_path, graphml_file)) #path for ./build
    if not os.path.exists(secure_filename(dir_path)):
        p1 = call(["./makestudy", makestudy_dir], cwd=concore_path)
        if(p1 == 0):
            resp = jsonify({'message': 'Directory successfully created'})
            resp.status_code = 201
        else:
            resp = jsonify({'message': 'There is an Error'})
            resp.status_code = 500        
    call(["./build"], cwd=dir_path)   
    return resp 


@app.route('/debug/<dir>', methods=['POST'])
def debug(dir):
    cur_path = os.getcwd()
    concore_path = os.path.abspath(os.path.join(cur_path, '../../'))
    dir_path = os.path.abspath(os.path.join(concore_path, dir))
    p1 = call(["./debug"], cwd=dir_path)
    if(p1 == 0):
        resp = jsonify({'message': 'Close the pop window after obtaing result'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'message': 'There is an Error'})
        resp.status_code = 500
        return resp  



# to download /download/<dir>?fetch=<downloadfile>. For example, /download/test?fetch=example.py.out&apikey=xyz
@app.route('/download/<dir>', methods=['POST', 'GET'])
def download(dir):
    download_file = request.args.get('fetch')
    apikey = request.args.get('apikey')
    dirname = dir + "_" + apikey

    if not os.path.exists(secure_filename(dirname)):
        resp = jsonify({'message': 'Directory not found'})
        resp.status_code = 400
        return resp

    try:
        return send_from_directory(secure_filename(dirname), download_file, as_attachment=True)
    except:
        resp = jsonify({'message': 'file not found'})
        resp.status_code = 400
        return resp
        
@app.route('/destroy/<dir>', methods=['POST'])
def destroy(dir):
    cur_path = os.getcwd()
    concore_path = os.path.abspath(os.path.join(cur_path, '../../'))
    p1 = call(["./destroy", dir], cwd=concore_path)
    if(p1 == 0):
        resp = jsonify({'message': 'Successfuly deleted Dirctory'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'message': 'There is an Error'})
        resp.status_code = 500
        return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0")
