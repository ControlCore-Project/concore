from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from subprocess import call
from pathlib import Path

EXECUTABLE_FOLDER = "./executable_files"
DOWNLOAD_FOLDER = "./download_files"
UPLOAD_FOLDER = "./uploaded_files"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['EXECUTABLE_FOLDER'] = EXECUTABLE_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER


@app.route('/upload', methods=['POST'])
def upload():
	if 'files[]' not in request.files:
		resp = jsonify({'message' : 'No file in the request'})
		resp.status_code = 400
		return resp
	
	files = request.files.getlist('files[]')
	
	errors = {}
	success = False
	
	for file in files:		
		if file:
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			success = True
	
	if success and errors:
		errors['message'] = 'File(s) successfully uploaded'
		resp = jsonify(errors)
		resp.status_code = 500
		return resp
	if success:
		resp = jsonify({'message' : 'Files successfully uploaded'})
		resp.status_code = 201
		return resp
	else:
		resp = jsonify(errors)
		resp.status_code = 500
		return resp


@app.route('/execute', methods=['POST'])
def execute():
	if 'file' not in request.files:
		resp = jsonify({'message' : 'No file in the request'})
		resp.status_code = 400
		return resp
	
	
	file = request.files['file']
	if file.filename == '':
		resp = jsonify({'message' : 'No file selected for Executing'})
		resp.status_code = 400
		return resp
	
	errors = {}
	success = False
	
			
	if file:
		filename = secure_filename(file.filename)
		file.save(os.path.join(app.config['EXECUTABLE_FOLDER'], filename))
		output_file = filename + ".out"
		path = app.config['EXECUTABLE_FOLDER']+"/"+filename 
		call(["python3", path, ">", output_file, "&"])
		success = True
	
	if success:
		resp = jsonify({'message' : 'Files successfully executed'})
		resp.status_code = 201
		return resp
	else:
		resp = jsonify(errors)
		resp.status_code = 500
		return resp



@app.route('/download/<file_name>', methods=['POST','GET'])
def download(file_name):
	try:	
		return send_from_directory(app.config["DOWNLOAD_FOLDER"], file_name, as_attachment=True)
	except:
		resp = jsonify({'message' : 'file not found'})
		resp.status_code = 400
		return resp	


if __name__ == "__main__":
    app.run(host="0.0.0.0")
