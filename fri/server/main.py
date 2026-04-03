from flask import Flask, request, jsonify, send_file, send_from_directory, abort
from werkzeug.utils import secure_filename
import xml.etree.ElementTree as ET
import os
import secrets
import subprocess
from subprocess import call,check_output
from pathlib import Path
import json
import logging
import platform
import re
import secrets
import threading
from flask_cors import CORS, cross_origin

logger = logging.getLogger(__name__)

# Input validation pattern for safe names (alphanumeric, dash, underscore, slash, dot, space)
SAFE_INPUT_PATTERN = re.compile(r'^[a-zA-Z0-9_\-/. ]+$')
# Pattern for filenames - no path separators or .. allowed
SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-. ]+$')

def validate_input(value, field_name, required=False):
    """Validate that input contains only safe characters."""
    if value is None:
        if required:
            raise ValueError(f"Missing required field: {field_name}")
        return True
    if not isinstance(value, str):
        raise ValueError(f"Invalid {field_name}: must be a string")
    if required and len(value) == 0:
        raise ValueError(f"Missing required field: {field_name}")
    if len(value) > 0 and not SAFE_INPUT_PATTERN.match(value):
        raise ValueError(f"Invalid {field_name}: contains unsafe characters")
    return True

def validate_filename(value, field_name, required=False):
    """Validate filename - no path separators or .. segments allowed."""
    if value is None:
        if required:
            raise ValueError(f"Missing required field: {field_name}")
        return True
    if not isinstance(value, str):
        raise ValueError(f"Invalid {field_name}: must be a string")
    if required and len(value) == 0:
        raise ValueError(f"Missing required field: {field_name}")
    # Reject path traversal attempts
    if '..' in value:
        raise ValueError(f"Invalid {field_name}: path traversal not allowed")
    # Use basename to strip any path components
    basename = os.path.basename(value)
    if basename != value:
        raise ValueError(f"Invalid {field_name}: must be a filename, not a path")
    if len(value) > 0 and not SAFE_FILENAME_PATTERN.match(value):
        raise ValueError(f"Invalid {field_name}: contains unsafe characters")
    return True

def validate_text_field(value, field_name, max_length=None):
    """Validate text fields like PR title/body - allow more characters but check type/length."""
    if value is None:
        return True
    if not isinstance(value, str):
        raise ValueError(f"Invalid {field_name}: must be a string")
    if max_length and len(value) > max_length:
        raise ValueError(f"Invalid {field_name}: too long (max {max_length} characters)")
    return True

def get_error_output(e):
    """Extract error output from CalledProcessError, preferring stderr then output."""
    raw_output = None
    if hasattr(e, 'stderr') and e.stderr:
        raw_output = e.stderr
    elif hasattr(e, 'output') and e.output:
        raw_output = e.output
    
    if raw_output is None:
        return "Command execution failed"
    
    if isinstance(raw_output, bytes):
        try:
            return raw_output.decode('utf-8', errors='replace')
        except Exception:
            return str(raw_output)
    elif isinstance(raw_output, str):
        return raw_output
    else:
        return str(raw_output)

cur_path = os.path.dirname(os.path.abspath(__file__))
concore_path = os.path.abspath(os.path.join(cur_path, '../../'))

# API key authentication for sensitive endpoints
API_KEY = os.environ.get("CONCORE_API_KEY")

def require_api_key():
    """Require a valid API key via X-API-KEY header."""
    if not API_KEY:
        abort(500, description="Server not configured with API key")
    provided = request.headers.get("X-API-KEY") or ""
    if not secrets.compare_digest(provided, API_KEY):
        abort(403, description="Unauthorized")

# Track single Jupyter process to prevent multiple concurrent launches
jupyter_process = None
jupyter_lock = threading.Lock()


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

if not app.secret_key:
    # In production, require an explicit secret key to avoid session issues
    flask_env = os.getenv("FLASK_ENV", "").lower()
    if flask_env in ("development", "dev") or app.debug:
        # Generate temporary key for development environments where a secret key
        # has not been explicitly configured.
        app.secret_key = secrets.token_hex(32)
    else:
        raise RuntimeError(
            "FLASK_SECRET_KEY environment variable must be set in production."
        )

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
        # Determine command name and error label based on docker flag
        if docker == 'true':
            cmd_name = "makedocker"
            error_label = "Docker study"
        else:
            cmd_name = "makestudy"
            error_label = "Study"

        # Build command list
        cmd = [cmd_name, makestudy_dir]
        if out_dir != None and out_dir != "":
            cmd.append(out_dir)

        # OS-specific adjustments
        is_windows = platform.uname()[0] == 'Windows'
        if not is_windows:
            cmd[0] = f"./{cmd[0]}"

        try:
            output_bytes = subprocess.check_output(cmd, cwd=concore_path, shell=is_windows)
            output_str = output_bytes.decode("utf-8")
            proc = 0
        except subprocess.CalledProcessError as e:
            output_str = f"{error_label} creation failed with return code {e.returncode} (check duplicate directory)"
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
            output_bytes = subprocess.check_output(r"./build", cwd=dir_path)
            output_str = output_str + output_bytes.decode("utf-8")
            resp = jsonify({'message': 'Directory successfully created', 'output': output_str})
        except subprocess.CalledProcessError as e:
            output_str = f"Build failed with return code {e.returncode}"
            resp = jsonify({'message': 'Build Failed', 'output': output_str})
            resp.status_code = 500
        if(maxtime != None and maxtime != ''):
            proc=call([r"./maxtime", maxtime], cwd=dir_path)
        if(params != None and params != ''):
            proc=call([r"./params", params], cwd=dir_path)
    return resp 

@app.route('/debug/<dir>', methods=['POST'])
def debug(dir):
    dir_name = secure_filename(dir)
    dir_path = os.path.abspath(os.path.join(concore_path, dir_name))
    if(platform.uname()[0]=='Windows'):
        proc = call(["debug"],shell=True, cwd=dir_path)
    else:
        proc = call([r"./debug"], cwd=dir_path)
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
        proc = call([r"./run"], cwd=dir_path)
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
        proc = call([r"./stop"], cwd=dir_path)
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
        proc = call([r"./clear"], cwd=dir_path)
        if(maxtime != None and maxtime != ''):
            proc = call([r"./maxtime", maxtime], cwd=dir_path)
        if(params != None and params != ''):
            proc = call([r"./params", params], cwd=dir_path)
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
        PR_TITLE = data.get('title') or ''
        PR_BODY = data.get('desc') or ''
        AUTHOR_NAME = data.get('auth') or ''
        STUDY_NAME = data.get('study') or ''
        STUDY_NAME_PATH = data.get('path') or ''
        BRANCH_NAME = data.get('branch') or ''
        
        # Validate all user inputs to prevent command injection
        # Strict validation for names/paths that go into command arguments
        validate_input(STUDY_NAME, 'study', required=True)
        validate_input(STUDY_NAME_PATH, 'path', required=True)
        validate_input(AUTHOR_NAME, 'auth', required=True)
        validate_input(BRANCH_NAME, 'branch', required=False)
        
        # For PR title/body, allow more characters but enforce type/length
        validate_text_field(PR_TITLE, 'title', max_length=512)
        validate_text_field(PR_BODY, 'desc', max_length=8192)
        
        # Build base command depending on platform
        if(platform.uname()[0]=='Windows'):
            cmd = ["cmd.exe", "/c", "contribute.bat", STUDY_NAME, STUDY_NAME_PATH, AUTHOR_NAME]
        else:
            cmd = [r"./contribute", STUDY_NAME, STUDY_NAME_PATH, AUTHOR_NAME]

        # Append optional branch/PR args only when BRANCH_NAME is provided
        if len(BRANCH_NAME) > 0:
            cmd.extend([BRANCH_NAME, PR_TITLE, PR_BODY])

        proc = subprocess.run(cmd, cwd=concore_path, check=True, capture_output=True, text=True)
        output_string = proc.stdout
        status=200
        if output_string.find("/pulls/")!=-1:
            status=200
        elif output_string.find("error")!=-1:
            status=501
        else:
            status=400
        return jsonify({'message': output_string}),status
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except subprocess.CalledProcessError as e:
        output_string = get_error_output(e)
        return jsonify({'message': output_string}), 501
    except Exception as e:
        output_string = "Some Error occured.Please try after some time"
        status=501
    return jsonify({'message': output_string}),status

# to download /download/<dir>?fetch=<downloadfile>. For example, /download/test?fetchDir=xyz&fetch=u
@app.route('/download/<dir>', methods=['POST', 'GET'])
def download(dir):
    download_file = request.args.get('fetch')
    sub_folder = request.args.get('fetchDir')

    if not download_file:
        abort(400, description="Missing file parameter")

    download_file = secure_filename(download_file)

    if download_file == "":
        abort(400, description="Invalid filename")

    # Normalize the requested file path
    safe_path = os.path.normpath(download_file)

    # Prevent absolute paths
    if os.path.isabs(safe_path):
        abort(400, description="Invalid file path")

    # Prevent directory traversal
    if ".." in safe_path.split(os.sep):
        abort(400, description="Directory traversal attempt detected")

    dirname = secure_filename(dir) + "/" + secure_filename(sub_folder)
    concore_real = os.path.realpath(concore_path)
    directory_name = os.path.realpath(os.path.join(concore_real, dirname))
    if not directory_name.startswith(concore_real + os.sep):
        abort(403, description="Access denied")
    if not os.path.exists(directory_name):
        resp = jsonify({'message': 'Directory not found'})
        resp.status_code = 400
        return resp

    # Ensure final resolved path is within the intended directory, resolving symlinks
    full_path = os.path.realpath(os.path.join(directory_name, safe_path))
    if not full_path.startswith(directory_name + os.sep):
        abort(403, description="Access denied")

    try:
        return send_from_directory(directory_name, safe_path, as_attachment=True)
    except Exception:
        resp = jsonify({'message': 'file not found'})
        resp.status_code = 400
        return resp

@app.route('/destroy/<dir>', methods=['DELETE'])
def destroy(dir):
    dir = secure_filename(dir)
    if(platform.uname()[0]=='Windows'):
        proc = call(["destroy", dir],shell=True, cwd=concore_path)
    else:
        proc = call([r"./destroy", dir], cwd=concore_path)
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
    
    # Validate user inputs to prevent command injection
    try:
        # Use strict filename validation - no path separators or .. allowed
        validate_filename(filename, 'filename', required=True)
        validate_input(library_path, 'path', required=False)
    except ValueError as e:
        resp = jsonify({'message': str(e)})
        resp.status_code = 400
        return resp
    
    if (library_path == None or library_path  == ''):
        library_path = r"../tools"
    try:
        if(platform.uname()[0]=='Windows'):
            # Use cmd.exe /c to invoke library.bat on Windows
            result = subprocess.run(["cmd.exe", "/c", r"..\library.bat", library_path, filename], cwd=dir_path, check=True, capture_output=True, text=True)
            proc = result.stdout
        else:
            proc = subprocess.check_output([r"../library", library_path, filename], cwd=dir_path, stderr=subprocess.STDOUT)
            proc = proc.decode("utf-8")
        resp = jsonify({'message': proc})
        resp.status_code = 200
        return resp
    except subprocess.CalledProcessError as e:
        error_output = get_error_output(e)
        resp = jsonify({'message': f'Command execution failed: {error_output}'})
        resp.status_code = 400
        return resp
    except Exception as e:
        resp = jsonify({'message': 'Internal server error'})
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
    global jupyter_process

    require_api_key()

    with jupyter_lock:
        if jupyter_process and jupyter_process.poll() is None:
            return jsonify({"message": "Jupyter already running"}), 409

        try:
            jupyter_process = subprocess.Popen(
                ['jupyter', 'lab', '--no-browser'],
                shell=False,
                cwd=concore_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return jsonify({"message": "Jupyter Lab started"}), 200
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.error("Failed to start Jupyter: %s", e)
            return jsonify({"error": "Failed to start Jupyter"}), 500


@app.route('/stopJupyter/', methods=['POST'])
def stopJupyter():
    global jupyter_process

    require_api_key()

    with jupyter_lock:
        if not jupyter_process or jupyter_process.poll() is not None:
            return jsonify({"message": "No running Jupyter instance"}), 404

        try:
            jupyter_process.terminate()
            # Wait for Jupyter to terminate gracefully
            jupyter_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if it did not exit in time
            jupyter_process.kill()
            jupyter_process.wait(timeout=5)
        finally:
            jupyter_process = None

        return jsonify({"message": "Jupyter stopped"}), 200


if __name__ == "__main__":
    # In production, use:
    # gunicorn -w 4 -b 0.0.0.0:5000 fri.server.main:app
    app.run(host="0.0.0.0", port=5000, debug=False)
