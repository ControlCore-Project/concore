# The script handles different environments: Docker, POSIX (macOS/Ubuntu), and Windows.
# It reads the graph nodes (representing computational tasks) and edges (representing data flow).
# Based on this information, it generates a directory structure and a set of helper scripts
# (build, run, stop, clear, maxtime, params, unlock) to manage the workflow.
# It also includes logic to handle "script specialization" for ZMQ-based communication,
# where it modifies source files to include specific port and port-name information.

# The script does the following:
# 1.  Initial Setup and Argument Parsing:
#     - Defines global constants for tool names (g++, iverilog, python3, matlab, etc.) and paths.
#     - Parses command-line arguments for the GraphML file, source directory, output directory, and execution type (posix, windows, docker).
#     - Checks for the existence of input/output directories and creates the output structure.
#     - Logs the configuration details.

# 2.  Graph Parsing and Adjacency Matrix Creation:
#     - Uses BeautifulSoup to parse the input GraphML file.
#     - Identifies nodes and edges, storing them in dictionaries.
#     - Creates a simple adjacency matrix (m) and a reachability matrix (ms) from the graph,
#       detecting any unreachable nodes and logging a warning.

# 3.  Script Specialization (Aggregation and Execution):
#     - This is a key part of the logic that handles ZMQ connections.
#     - It iterates through the edges, specifically looking for ones with labels in the format "0x<hex_port>_<port_name>".
#     - It aggregates these port parameters for each node.
#     - It then uses an external script `copy_with_port_portname.py` to "specialize" the original source files. This means it creates
#       new versions of the scripts, injecting the ZMQ port information directly into the code.
#     - The `nodes_dict` is then updated to point to these newly created, specialized scripts.

# 4.  Port Mapping and File Generation:
#     - Generates `.iport` (input port) and `.oport` (output port) mapping files for each node.
#     - These files are simple dictionaries that map volume names (for file-based communication) or port names (for ZMQ)
#       to their corresponding port numbers or indices. This allows the individual scripts to know how to connect to their
#       peers in the graph.

# 5.  File Copying and Script Generation:
#     - Copies all necessary source files (`.py`, `.cpp`, `.m`, etc.) from the source directory to the `outdir/src` directory.
#     - Handles cases where specialized scripts were created, ensuring the new files are copied instead of the originals.
#     - Copies a set of standard `concore` files (`.py`, `.hpp`, `.v`, `.m`, `mkcompile`) into the `src` directory.

# 6.  Environment-Specific Scripting (Main Logic Branches):
#     - This is the largest and most complex part, where the script's behavior diverges based on the `concoretype`.

#     a. Docker:
#         - Generates `Dockerfile`s for each node's container. If a custom Dockerfile exists in the source directory, it's used.
#           Otherwise, it generates a default one based on the file extension (`.py`, `.cpp`, etc.).
#         - Creates `build.bat` (Windows) or `build` (POSIX) scripts to build the Docker images for each node.
#         - Creates `run.bat`/`run` scripts to launch the containers, setting up the necessary shared volumes (`-v`) for data transfer.
#         - Creates `stop.bat`/`stop` and `clear.bat`/`clear` scripts to manage the containers and clean up the volumes.
#         - Creates helper scripts like `maxtime.bat`/`maxtime`, `params.bat`/`params`, and `unlock.bat`/`unlock` to
#           pass runtime parameters or API keys to the containers.

#     b. POSIX (Linux/macOS) and Windows:
#         - These branches handle direct execution on the host machine without containers.
#         - Creates a separate directory for each node inside the output directory.
#         - Uses the `build` script to copy source files and create symbolic links (`ln -s` on POSIX, `mklink` on Windows)
#           between the node directories and the shared data directories (representing graph edges).
#         - Generates `run` and `debug` scripts to execute the programs. It uses platform-specific commands
#           like `start /B` for Windows and `xterm -e` or `osascript` for macOS to run the processes.
#         - The `stop` and `clear` scripts use `kill` or `del` commands to manage the running processes and files.
#         - Generates `maxtime`, `params`, and `unlock` scripts that directly write files to the shared directories.

# 7.  Permissions:
#     - Sets the executable permission (`stat.S_IRWXU`) for the generated scripts on POSIX systems.

from bs4 import BeautifulSoup
import atexit
import logging
import re
import sys
import os
import shutil
import stat
import copy_with_port_portname
import numpy as np
import shlex  # Added for POSIX shell escaping

# input validation helper
def safe_name(value, context, allow_path=False):
    """
    Validates that the input string does not contain characters dangerous 
    for filesystem paths or shell command injection.
    """
    if not value:
        raise ValueError(f"{context} cannot be empty")
    # blocks control characters and shell metacharacters
    # allow path separators and drive colons for full paths when needed
    if allow_path:
        pattern = r'[\x00-\x1F\x7F*?"<>|;&`$\'()]'
    else:
        # blocks path traversal (/, \, :) in addition to shell metacharacters
        pattern = r'[\x00-\x1F\x7F\\/:*?"<>|;&`$\'()]'
    if re.search(pattern, value):
        raise ValueError(f"Unsafe {context}: '{value}' contains illegal characters.")
    return value

def safe_relpath(value, context):
    """
    Allow relative subpaths while blocking traversal and absolute/drive paths.
    """
    if not value:
        raise ValueError(f"{context} cannot be empty")
    normalized = value.replace("\\", "/")
    safe_name(normalized, context, allow_path=True)
    if normalized.startswith("/") or normalized.startswith("~"):
        raise ValueError(f"Unsafe {context}: absolute paths are not allowed.")
    if re.match(r"^[A-Za-z]:", normalized):
        raise ValueError(f"Unsafe {context}: drive paths are not allowed.")
    if ":" in normalized:
        raise ValueError(f"Unsafe {context}: ':' is not allowed in relative paths.")
    if any(part in ("", "..") for part in normalized.split("/")):
        raise ValueError(f"Unsafe {context}: invalid path segment.")
    return normalized

MKCONCORE_VER = "22-09-18"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def _load_tool_config(filepath):
    tools = {}
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if v:
                tools[k] = v
    return tools

def _resolve_concore_path():
    script_concore = os.path.join(SCRIPT_DIR, "concore.py")
    if os.path.exists(script_concore):
        return SCRIPT_DIR
    cwd_concore = os.path.join(os.getcwd(), "concore.py")
    if os.path.exists(cwd_concore):
        return os.getcwd()
    return SCRIPT_DIR

if len(sys.argv) < 4:
    print("usage: py mkconcore.py file.graphml sourcedir outdir [type]")
    print(" type must be posix (macos or ubuntu), windows, or docker")
    sys.exit(1)

GRAPHML_FILE = sys.argv[1]
TRIMMED_LOGS = True
CONCOREPATH = _resolve_concore_path()
CPPWIN    = os.environ.get("CONCORE_CPPWIN", "g++")          #Windows C++  6/22/21
CPPEXE    = os.environ.get("CONCORE_CPPEXE", "g++")          #Ubuntu/macOS C++  6/22/21
VWIN      = os.environ.get("CONCORE_VWIN", "iverilog")       #Windows verilog  6/25/21
VEXE      = os.environ.get("CONCORE_VEXE", "iverilog")       #Ubuntu/macOS verilog  6/25/21
PYTHONEXE = os.environ.get("CONCORE_PYTHONEXE", "python3")   #Ubuntu/macOS python3
PYTHONWIN = os.environ.get("CONCORE_PYTHONWIN", "python")    #Windows python3
MATLABEXE = os.environ.get("CONCORE_MATLABEXE", "matlab")    #Ubuntu/macOS matlab
MATLABWIN = os.environ.get("CONCORE_MATLABWIN", "matlab")    #Windows matlab
OCTAVEEXE = os.environ.get("CONCORE_OCTAVEEXE", "octave")    #Ubuntu/macOS octave
OCTAVEWIN = os.environ.get("CONCORE_OCTAVEWIN", "octave")    #Windows octave
M_IS_OCTAVE = False      #treat .m as octave
MCRPATH  = "~/MATLAB/R2021a" #path to local Ubunta Matlab Compiler Runtime
DOCKEREXE = "sudo docker"#assume simple docker install
DOCKEREPO = "markgarnold"#where pulls come from 3/28/21
INDIRNAME = ":/in"
OUTDIRNAME = ":/out"

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s' if TRIMMED_LOGS else '%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

if os.path.exists(CONCOREPATH+"/concore.octave"):
    M_IS_OCTAVE = True       #treat .m as octave 9/27/21

if os.path.exists(CONCOREPATH+"/concore.mcr"): # 11/12/21
    with open(CONCOREPATH+"/concore.mcr", "r") as f:
        MCRPATH = f.readline().strip() #path to local Ubunta Matlab Compiler Runtime
    
if os.path.exists(CONCOREPATH+"/concore.sudo"): # 12/04/21
    with open(CONCOREPATH+"/concore.sudo", "r") as f:
        DOCKEREXE = f.readline().strip() #to omit sudo in docker

if os.path.exists(CONCOREPATH+"/concore.repo"): # 12/04/21
    with open(CONCOREPATH+"/concore.repo", "r") as f:
        DOCKEREPO = f.readline().strip() #docker id for repo

if os.path.exists(CONCOREPATH+"/concore.tools"):
    _tools = _load_tool_config(CONCOREPATH+"/concore.tools")
    CPPWIN    = _tools.get("CPPWIN", CPPWIN)
    CPPEXE    = _tools.get("CPPEXE", CPPEXE)
    VWIN      = _tools.get("VWIN", VWIN)
    VEXE      = _tools.get("VEXE", VEXE)
    PYTHONEXE = _tools.get("PYTHONEXE", PYTHONEXE)
    PYTHONWIN = _tools.get("PYTHONWIN", PYTHONWIN)
    MATLABEXE = _tools.get("MATLABEXE", MATLABEXE)
    MATLABWIN = _tools.get("MATLABWIN", MATLABWIN)
    OCTAVEEXE = _tools.get("OCTAVEEXE", OCTAVEEXE)
    OCTAVEWIN = _tools.get("OCTAVEWIN", OCTAVEWIN)

prefixedgenode = ""
sourcedir = sys.argv[2]
outdir = sys.argv[3]

# Validate outdir argument (allow full paths)
safe_name(outdir, "Output directory argument", allow_path=True)

if not os.path.isdir(sourcedir):
    logging.error(f"{sourcedir} does not exist")
    quit()

if len(sys.argv) == 4:
    prefixedgenode = outdir+"_" #nodes and edges prefixed with outdir_ only in case no type specified 3/24/21
    concoretype = "docker"
else:
    concoretype = sys.argv[4]
    if not (concoretype in ["posix","windows","docker","macos","ubuntu"]):
        logging.error(" type must be posix (macos or ubuntu), windows, or docker")
        quit()
ubuntu = False #6/24/21
if concoretype == "ubuntu":
    concoretype = "posix"
    ubuntu = True
if concoretype == "macos":
    concoretype = "posix"

if os.path.exists(outdir):
    logging.error(f"{outdir} already exists")
    logging.error(f"if intended, Remove/Rename {outdir} first")
    quit()

os.mkdir(outdir)
os.chdir(outdir)
if concoretype == "windows":
    fbuild = open("build.bat","w")
    frun = open("run.bat", "w")
    fdebug = open("debug.bat", "w")
    fstop = open("stop.bat", "w")  #3/27/21
    fclear = open("clear.bat", "w") 
    fmaxtime = open("maxtime.bat", "w") # 9/12/21
    funlock = open("unlock.bat", "w") # 12/4/21
    fparams = open("params.bat", "w") # 9/18/22

else:
    fbuild = open("build","w")
    frun = open("run", "w")
    fdebug = open("debug", "w")
    fstop = open("stop", "w")  #3/27/21
    fclear = open("clear", "w") 
    fmaxtime = open("maxtime", "w") # 9/12/21
    funlock = open("unlock", "w") # 12/4/21
    fparams = open("params", "w") # 9/18/22

def cleanup_script_files():
    for fh in [fbuild, frun, fdebug, fstop, fclear, fmaxtime, funlock, fparams]:
        if not fh.closed:
            fh.close()
atexit.register(cleanup_script_files)

os.mkdir("src")
os.chdir("..")

logging.info(f"mkconcore {MKCONCORE_VER}")
logging.info(f"Concore path: {CONCOREPATH}")
logging.info(f"graphml input: {GRAPHML_FILE}")
logging.info(f"source directory: {sourcedir}")
logging.info(f"output directory: {outdir}")
logging.info(f"control core type: {concoretype}")
logging.info(f"treat .m as octave: {str(M_IS_OCTAVE)}")
logging.info(f"MCR path: {MCRPATH}")
logging.info(f"Docker repository: {DOCKEREPO}")

with open(GRAPHML_FILE, "r") as f:
    text_str = f.read()

soup = BeautifulSoup(text_str, 'xml')

edges_text = soup.find_all('edge')
nodes_text = soup.find_all('node')

# Store the edges and nodes in a dictionary
edge_label_regex = re.compile(r"0x([a-fA-F0-9]+)_(\S+)")
edges_dict = dict()
nodes_dict = dict()
node_id_to_label_map = dict() # Helper to get clean node labels from GraphML ID

for node in nodes_text:
    try:
        data = node.find('data', recursive=False)
        if data:
            node_label_tag = data.find('y:NodeLabel')
            if node_label_tag:
                node_label = prefixedgenode + node_label_tag.text
                node_label = re.sub(r'(\s+|\n)', ' ', node_label)
                
                #Validate node labels
                if ':' in node_label:
                    container_part, source_part = node_label.split(':', 1)
                    safe_name(container_part, f"Node container name '{container_part}'")
                    source_part = safe_relpath(source_part, f"Node source file '{source_part}'")
                    node_label = f"{container_part}:{source_part}"
                else:
                    safe_name(node_label, f"Node label '{node_label}'")
                    # Explicitly reject incorrect format to prevent later crashes and ambiguity
                    raise ValueError(f"Invalid node label '{node_label}': expected format 'container:source' with a ':' separator.")

                nodes_dict[node['id']] = node_label
                node_id_to_label_map[node['id']] = node_label.split(':')[0]
    except (IndexError, AttributeError):
        logging.debug('A node with no valid properties encountered and ignored')

label_values = list(nodes_dict.values())
duplicates = {label for label in label_values if label_values.count(label) > 1}
if duplicates:
    logging.error(f"Duplicate node labels found: {sorted(duplicates)}")
    quit()

for edge in edges_text:
    try:
        data = edge.find('data', recursive=False)
        if data:
            edge_label_tag = data.find('y:EdgeLabel')
            if edge_label_tag:
                raw_label = edge_label_tag.text
                edge_label = prefixedgenode + raw_label
                # Filter out ZMQ edges from the file-based edge dictionary by checking the raw label
                if not edge_label_regex.match(raw_label):
                    
                    #Validate edge labels
                    safe_name(edge_label, f"Edge label '{edge_label}'")

                    if edge_label not in edges_dict:
                        edges_dict[edge_label] = [nodes_dict[edge['source']], []]
                    edges_dict[edge_label][1].append(nodes_dict[edge['target']])
    except (IndexError, AttributeError, KeyError):
        logging.debug('An edge with no valid properties or missing node encountered and ignored')


############## Mark's Docker
logging.info("Building graph adjacency matrix...")
nodes_num = {label: i for i, label in enumerate(nodes_dict.values())}

m = np.zeros((len(nodes_dict), len(nodes_dict)))
for edges in edges_dict:
   source_node_label = edges_dict[edges][0]
   for dest_node_label in edges_dict[edges][1]:
      try:
          source_idx = nodes_num[source_node_label]
          dest_idx = nodes_num[dest_node_label]
          m[source_idx][dest_idx] = 1
      except KeyError as e:
          logging.error(f"KeyError while building matrix. Label '{e}' not found in node map.")
          continue

mp = np.eye(len(nodes_dict))
ms = np.zeros((len(nodes_dict),len(nodes_dict)))
for i in range(len(nodes_dict)):
  mp = mp@m
  ms += mp
if (ms == 0).any():
  logging.warning("Unreachable nodes detected")

# --- START: New logic for script specialization (Aggregation) ---
python_executable = sys.executable
mkconcore_dir = os.path.dirname(os.path.abspath(__file__))
copy_script_py_path = os.path.join(mkconcore_dir, "copy_with_port_portname.py")
if not os.path.exists(copy_script_py_path):
    copy_script_py_path = os.path.join(CONCOREPATH, "copy_with_port_portname.py")

if not os.path.exists(copy_script_py_path):
    logging.warning(f"copy_with_port_portname.py not found. Script specialization will be skipped.")
    copy_script_py_path = None

# Dictionary to aggregate edge parameters for each node that needs specialization
# Key: node_id (from GraphML), Value: list of edge parameter dicts
node_edge_params = {}
edge_label_regex = re.compile(r"0x([^_]+)_(\S+)")

logging.info("Aggregating ZMQ edge parameters for nodes...")
if copy_script_py_path:
    for edge_element in soup.find_all('edge'):
        try:
            edge_label_tag = edge_element.find('y:EdgeLabel')
            if not edge_label_tag or not edge_label_tag.text:
                continue
            
            raw_edge_label = edge_label_tag.text
            match = edge_label_regex.match(raw_edge_label)

            if match:
                hex_port_val, port_name_val = match.groups()
                # Convert hex port value to decimal string
                try:
                    decimal_port_str = str(int(hex_port_val, 16))
                except ValueError:
                    logging.error(f"Invalid hex value '{hex_port_val}' in edge label. Using as is.")
                    decimal_port_str = hex_port_val

                source_node_id = edge_element['source']
                target_node_id = edge_element['target']

                # Get clean labels for use in variable names
                source_node_label = node_id_to_label_map.get(source_node_id, "UNKNOWN_SOURCE")
                target_node_label = node_id_to_label_map.get(target_node_id, "UNKNOWN_TARGET")

                logging.info(f"Found ZMQ edge '{raw_edge_label}' from '{source_node_label}' to '{target_node_label}'")

                edge_param_data = {
                    "port": decimal_port_str,
                    "port_name": port_name_val,
                    "source_node_label": source_node_label,
                    "target_node_label": target_node_label
                }

                # Add this edge's data to both the source and target nodes for specialization
                if source_node_id in nodes_dict:
                    if source_node_id not in node_edge_params:
                        node_edge_params[source_node_id] = []
                    node_edge_params[source_node_id].append(edge_param_data)

                if target_node_id in nodes_dict:
                    if target_node_id not in node_edge_params:
                        node_edge_params[target_node_id] = []
                    node_edge_params[target_node_id].append(edge_param_data)
        except Exception as e:
            logging.warning(f"Error processing edge for parameter aggregation: {e}")

# --- Now, run the specialization for each node that has aggregated parameters ---
if node_edge_params:
    logging.info("Running script specialization process...")
    specialized_scripts_output_dir = os.path.abspath(os.path.join(outdir, "src"))
    os.makedirs(specialized_scripts_output_dir, exist_ok=True)

    for node_id, params_list in node_edge_params.items():
        current_node_full_label = nodes_dict[node_id]
        try:
            container_name, original_script = current_node_full_label.split(':', 1)
        except ValueError:
            continue # Skip if label format is wrong

        if not original_script or "." not in original_script:
            continue # Skip if not a script file

        template_script_full_path = os.path.join(sourcedir, original_script)
        if not os.path.exists(template_script_full_path):
            logging.error(f"Cannot specialize: Original script '{template_script_full_path}' not found in '{sourcedir}'.")
            continue

        new_script_basename = copy_with_port_portname.run_specialization_script(
            template_script_full_path,
            specialized_scripts_output_dir,
            params_list,
            python_executable,
            copy_script_py_path
        )

        if new_script_basename:
            # Update nodes_dict to point to the new comprehensive specialized script
            nodes_dict[node_id] = f"{container_name}:{new_script_basename}"
            logging.info(f"Node ID '{node_id}' ('{container_name}') updated to use specialized script '{new_script_basename}'.")
        else:
            logging.error(f"Failed to generate specialized script for node ID '{node_id}'. It will retain its original script.")

#not right for PM2_1_1 and PM2_1_2
volswr = len(nodes_dict)*['']
i = 0
for edges in edges_dict:
  volswr[nodes_num[edges_dict[edges][0]]] += ' -v '+str(edges)+OUTDIRNAME+str(volswr[nodes_num[edges_dict[edges][0]]].count('-v')+1)
  i += 1


#save indir
indir = len(nodes_dict)*[[]]
volsro = len(nodes_dict)*['']
i = 0
for edges in edges_dict:
   for dest in (edges_dict[edges])[1]:
     incount = volsro[nodes_num[dest]].count('-v')
     volIndirPair = str(edges)+INDIRNAME+str(incount+1)
     indir[nodes_num[dest]] = indir[nodes_num[dest]] + [volIndirPair]
     volsro[nodes_num[dest]] += ' -v '+volIndirPair+':ro'
     i += 1

# copy sourcedir into ./src
# --- Modified file copying loop ---
logging.info("Processing files for nodes...")
for node_id_key in list(nodes_dict.keys()):
    node_label_from_dict = nodes_dict[node_id_key]
    try:
        containername, sourcecode = node_label_from_dict.split(':', 1)
    except ValueError:
        continue

    if not sourcecode:
        continue

    if "." in sourcecode:
        dockername, langext = os.path.splitext(sourcecode)
    else:
        dockername, langext = sourcecode, ""
    
    script_target_path = os.path.join(outdir, "src", sourcecode)
    script_target_parent = os.path.dirname(script_target_path)
    if script_target_parent:
        os.makedirs(script_target_parent, exist_ok=True)

    # If the script was specialized, it's already in outdir/src. If not, copy from sourcedir.
    if node_id_key not in node_edge_params:
        script_source_path = os.path.join(sourcedir, sourcecode)
        if os.path.exists(script_source_path):
            shutil.copy2(script_source_path, script_target_path)
        else:
            logging.error(f"Script '{sourcecode}' not found in sourcedir '{sourcedir}'")

    # The rest of the file handling (Dockerfiles, .dir) uses 'dockername',
    # which is now derived from the specialized script name, maintaining consistency.
    if concoretype == "docker":
        custom_dockerfile = f"Dockerfile.{dockername}"
        if os.path.exists(os.path.join(sourcedir, custom_dockerfile)):
            shutil.copy2(os.path.join(sourcedir, custom_dockerfile), os.path.join(outdir, "src", custom_dockerfile))
    
    dir_for_node = f"{dockername}.dir"
    if os.path.isdir(os.path.join(sourcedir, dir_for_node)):
        shutil.copytree(os.path.join(sourcedir, dir_for_node), os.path.join(outdir, "src", dir_for_node), dirs_exist_ok=True)


#copy proper concore.py into /src
try:
    if concoretype=="docker":
        with open(CONCOREPATH+"/concoredocker.py") as fsource:
            source_content = fsource.read()
    else:
        with open(CONCOREPATH+"/concore.py") as fsource:
            source_content = fsource.read()
except (FileNotFoundError, IOError) as e:
    logging.error(f"{CONCOREPATH} is not correct path to concore: {e}")
    quit()
with open(outdir+"/src/concore.py","w") as fcopy:
    fcopy.write(source_content)

#copy proper concore.hpp into /src 6/22/21
try:
    if concoretype=="docker":
        with open(CONCOREPATH+"/concoredocker.hpp") as fsource:
            source_content = fsource.read()
    else:
        with open(CONCOREPATH+"/concore.hpp") as fsource:
            source_content = fsource.read()
except (FileNotFoundError, IOError) as e:
    logging.error(f"{CONCOREPATH} is not correct path to concore: {e}")
    quit()
with open(outdir+"/src/concore.hpp","w") as fcopy:
    fcopy.write(source_content)

#copy proper concore.v into /src 6/25/21
try:
    if concoretype=="docker":
        with open(CONCOREPATH+"/concoredocker.v") as fsource:
            source_content = fsource.read()
    else:
        with open(CONCOREPATH+"/concore.v") as fsource:
            source_content = fsource.read()
except (FileNotFoundError, IOError) as e:
    logging.error(f"{CONCOREPATH} is not correct path to concore: {e}")
    quit()
with open(outdir+"/src/concore.v","w") as fcopy:
    fcopy.write(source_content)

#copy mkcompile into /src  5/27/21
try:
    with open(CONCOREPATH+"/mkcompile") as fsource:
        source_content = fsource.read()
except (FileNotFoundError, IOError) as e:
    logging.error(f"{CONCOREPATH} is not correct path to concore: {e}")
    quit()
with open(outdir+"/src/mkcompile","w") as fcopy:
    fcopy.write(source_content)
os.chmod(outdir+"/src/mkcompile",stat.S_IRWXU)

#copy concore*.m into /src  4/2/21
try: #maxtime in matlab 11/22/21
    with open(CONCOREPATH+"/concore_default_maxtime.m") as fsource:
        source_content = fsource.read()
except (FileNotFoundError, IOError) as e:
    logging.error(f"{CONCOREPATH} is not correct path to concore: {e}")
    quit()
with open(outdir+"/src/concore_default_maxtime.m","w") as fcopy:
    fcopy.write(source_content)
try:
    with open(CONCOREPATH+"/concore_unchanged.m") as fsource:
        source_content = fsource.read()
except (FileNotFoundError, IOError) as e:
    logging.error(f"{CONCOREPATH} is not correct path to concore: {e}")
    quit()
with open(outdir+"/src/concore_unchanged.m","w") as fcopy:
    fcopy.write(source_content)
try:
    with open(CONCOREPATH+"/concore_read.m") as fsource:
        source_content = fsource.read()
except (FileNotFoundError, IOError) as e:
    logging.error(f"{CONCOREPATH} is not correct path to concore: {e}")
    quit()
with open(outdir+"/src/concore_read.m","w") as fcopy:
    fcopy.write(source_content)
try:
    with open(CONCOREPATH+"/concore_write.m") as fsource:
        source_content = fsource.read()
except (FileNotFoundError, IOError) as e:
    logging.error(f"{CONCOREPATH} is not correct path to concore: {e}")
    quit()
with open(outdir+"/src/concore_write.m","w") as fcopy:
    fcopy.write(source_content)
try: #4/9/21
    with open(CONCOREPATH+"/concore_initval.m") as fsource:
        source_content = fsource.read()
except (FileNotFoundError, IOError) as e:
    logging.error(f"{CONCOREPATH} is not correct path to concore: {e}")
    quit()
with open(outdir+"/src/concore_initval.m","w") as fcopy:
    fcopy.write(source_content)
try: #11/19/21
    with open(CONCOREPATH+"/concore_iport.m") as fsource:
        source_content = fsource.read()
except (FileNotFoundError, IOError) as e:
    logging.error(f"{CONCOREPATH} is not correct path to concore: {e}")
    quit()
with open(outdir+"/src/concore_iport.m","w") as fcopy:
    fcopy.write(source_content)
try: #11/19/21
    with open(CONCOREPATH+"/concore_oport.m") as fsource:
        source_content = fsource.read()
except (FileNotFoundError, IOError) as e:
    logging.error(f"{CONCOREPATH} is not correct path to concore: {e}")
    quit()
with open(outdir+"/src/concore_oport.m","w") as fcopy:
    fcopy.write(source_content)
try: # 4/4/21
    if concoretype=="docker":
        with open(CONCOREPATH+"/import_concoredocker.m") as fsource:
            source_content = fsource.read()
    else:
        with open(CONCOREPATH+"/import_concore.m") as fsource:
            source_content = fsource.read()
except (FileNotFoundError, IOError) as e:
    logging.error(f"{CONCOREPATH} is not correct path to concore: {e}")
    quit()
with open(outdir+"/src/import_concore.m","w") as fcopy:
    fcopy.write(source_content)

# --- Generate iport and oport mappings ---
logging.info("Generating iport/oport mappings...")
node_port_mappings = {label: {'iport': {}, 'oport': {}} for label in nodes_dict.values()}
# 1. Process file-based inputs
node_labels_by_index = {i: label for label, i in nodes_num.items()}
for i, in_dirs in enumerate(indir):
    if i in node_labels_by_index:
        node_label = node_labels_by_index[i]
        for pair in in_dirs:
            volname, portnum = pair.split(INDIRNAME)
            node_port_mappings[node_label]['iport'][volname] = int(portnum)
# 2. Process file-based outputs
for edge_label, (source_label, target_labels) in edges_dict.items():
    if source_label in node_port_mappings:
        out_count = len(node_port_mappings[source_label]['oport']) + 1
        node_port_mappings[source_label]['oport'][edge_label] = out_count
# 3. Augment with bidirectional ZMQ connections
logging.info("Augmenting port maps with ZMQ connections...")
for edge_element in soup.find_all('edge'):
    try:
        edge_label_tag = edge_element.find('y:EdgeLabel')
        if not edge_label_tag or not edge_label_tag.text: continue
        match = edge_label_regex.match(edge_label_tag.text)
        if match:
            hex_port_val, port_name_val = match.groups()
            # Convert hex port value to decimal string
            try:
                decimal_port_str = str(int(hex_port_val, 16))
            except ValueError:
                logging.error(f"Invalid hex value '{hex_port_val}' in edge label. Using as is.")
                decimal_port_str = hex_port_val

            source_label = nodes_dict.get(edge_element['source'])
            target_label = nodes_dict.get(edge_element['target'])
            if source_label and target_label:
                node_port_mappings[source_label]['iport'][port_name_val] = decimal_port_str
                node_port_mappings[source_label]['oport'][port_name_val] = decimal_port_str
                node_port_mappings[target_label]['iport'][port_name_val] = decimal_port_str
                node_port_mappings[target_label]['oport'][port_name_val] = decimal_port_str
                logging.info(f"  - Added ZMQ port '{port_name_val}:{decimal_port_str}' to both iport/oport for nodes '{source_label}' and '{target_label}'")
    except Exception as e:
        logging.warning(f"Error processing ZMQ edge for port map: {e}")

# 4. Write final iport/oport files
logging.info("Writing .iport and .oport files...")
for node_label, ports in node_port_mappings.items():
    try:
        containername, sourcecode = node_label.split(':', 1)
        if not sourcecode or "." not in sourcecode: continue
        dockername = os.path.splitext(sourcecode)[0]
        iport_path = os.path.join(outdir, "src", f"{dockername}.iport")
        oport_path = os.path.join(outdir, "src", f"{dockername}.oport")
        iport_parent = os.path.dirname(iport_path)
        if iport_parent:
            os.makedirs(iport_parent, exist_ok=True)
        with open(iport_path, "w") as fport:
            fport.write(str(ports['iport']).replace("'" + prefixedgenode, "'"))
        with open(oport_path, "w") as fport:
            fport.write(str(ports['oport']).replace("'" + prefixedgenode, "'"))
    except ValueError:
        continue


#if docker, make docker-dirs, generate build, run, stop, clear scripts and quit
if (concoretype=="docker"):
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0 and sourcecode.find(".")!=-1: #3/28/21
            dockername,langext = sourcecode.rsplit(".", 1)
            dockerfile_path = os.path.join(outdir, "src", f"Dockerfile.{dockername}")
            if not os.path.exists(dockerfile_path): # 3/30/21
                try:
                    if langext=="py":
                        src_path = CONCOREPATH+"/Dockerfile.py"
                        logging.info("assuming .py extension for Dockerfile")
                    elif langext == "cpp":  # 6/22/21
                        src_path = CONCOREPATH+"/Dockerfile.cpp"
                        logging.info("assuming .cpp extension for Dockerfile")
                    elif langext == "v":  # 6/26/21
                        src_path = CONCOREPATH+"/Dockerfile.v"
                        logging.info("assuming .v extension for Dockerfile")
                    elif langext == "sh":  # 5/19/21
                        src_path = CONCOREPATH+"/Dockerfile.sh"
                        logging.info("assuming .sh extension for Dockerfile")
                    else:
                        src_path = CONCOREPATH+"/Dockerfile.m"
                        logging.info("assuming .m extension for Dockerfile")
                    with open(src_path) as fsource:
                        source_content = fsource.read()
                except:
                    logging.error(f"{CONCOREPATH} is not correct path to concore")
                    quit()
                dockerfile_parent = os.path.dirname(dockerfile_path)
                if dockerfile_parent:
                    os.makedirs(dockerfile_parent, exist_ok=True)
                with open(dockerfile_path,"w") as fcopy:
                    fcopy.write(source_content)
                    if langext=="py":
                        fcopy.write('CMD ["python", "-i", "'+sourcecode+'"]\n')
                    if langext=="m":
                        fcopy.write('CMD ["octave", "-qf", "--eval", "run('+"'"+sourcecode+"'"+')"]\n') #3/28/21
                    if langext=="sh":
                        fcopy.write('CMD ["./'+sourcecode+'" ,"/opt/mcr/v910"]')  # 5/19/21
                    #["./run_pmmat.sh", "/opt/mcr/MATLAB/MATLAB_Runtime/v910"]
                    if langext=="v":
                        fcopy.write('RUN iverilog ./'+sourcecode+'\n')  # 7/02/21
                        fcopy.write('CMD ["./a.out"]\n')  # 7/02/21

    fbuild.write('#!/bin/bash' + "\n")
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0 and sourcecode.find(".")!=-1: #3/28/21
            dockername,langext = sourcecode.rsplit(".", 1)
            fbuild.write("mkdir docker-"+dockername+"\n")
            fbuild.write("cd docker-"+dockername+"\n")
            fbuild.write("cp ../src/Dockerfile."+dockername+" Dockerfile\n")
            #copy sourcefiles from ./src into corresponding directories
            fbuild.write("cp ../src/"+sourcecode+" .\n")
            if langext == "py": #4/29/21
                fbuild.write("cp ../src/concore.py .\n")
            elif langext == "cpp": #6/22/21
                fbuild.write("cp ../src/concore.hpp .\n")
            elif langext == "v": #6/25/21
                fbuild.write("cp ../src/concore.v .\n")
            if langext == "m":
                fbuild.write("cp ../src/concore_*.m .\n")
                fbuild.write("cp ../src/import_concore.m .\n")
            if langext == "sh": #5/27/21
                fbuild.write("chmod u+x "+sourcecode+"\n")
            fbuild.write("cp ../src/"+dockername+".iport concore.iport\n")
            fbuild.write("cp ../src/"+dockername+".oport concore.oport\n")
            #include data files in here if they exist
            if os.path.isdir(sourcedir+"/"+dockername+".dir"):
                fbuild.write("cp -r ../src/"+dockername+".dir/* .\n")
            fbuild.write(DOCKEREXE+" build -t docker-"+dockername+" .\n")
            fbuild.write("cd ..\n")              

    fbuild.close()

    frun.write('#!/bin/bash' + "\n")
    i=0
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            safe_container = shlex.quote(containername) 
            if sourcecode.find(".")==-1:
                logging.debug(f"Generating Docker run command: {DOCKEREXE} run --name={containername+volswr[i]+volsro[i]} {DOCKEREPO}/docker- {sourcecode}")
                # Use safe_container
                frun.write(DOCKEREXE+' run --name='+safe_container+volswr[i]+volsro[i]+" "+DOCKEREPO+"/docker-"+shlex.quote(sourcecode)+"&\n")
            else:    
                dockername,langext = sourcecode.rsplit(".", 1)
                logging.debug(f"Generating Docker run command for {dockername}: {DOCKEREXE} run --name={containername+volswr[i]+volsro[i]} docker-{dockername}")
                # Use safe_container
                frun.write(DOCKEREXE+' run --name='+safe_container+volswr[i]+volsro[i]+" docker-"+shlex.quote(dockername)+"&\n")
        i=i+1
    frun.close()

    fstop.write('#!/bin/bash' + "\n")
    i=0 #  3/27/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            #dockername,langext = sourcecode.rsplit(".", 1)
            dockername = sourcecode.rsplit(".", 1)[0] # 3/28/21
            safe_container = shlex.quote(containername)
            fstop.write(DOCKEREXE+' stop '+safe_container+"\n")
            fstop.write(DOCKEREXE+' rm '+safe_container+"\n")
        i=i+1
    fstop.close()

    fclear.write('#!/bin/bash' + "\n")
    i=0 #  9/13/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            dockername = sourcecode.rsplit(".", 1)[0] #3/28/21
            writeedges = volswr[i]
            while writeedges.find(":") != -1: 
                #scape volume path using shlex.quote for Docker commands (defense-in-depth)
                volume_path = writeedges.split(":")[0].split("-v")[1].strip()
                fclear.write(DOCKEREXE+' volume rm ' + shlex.quote(volume_path) +"\n") # Added strip() and quote
                writeedges = writeedges[writeedges.find(":")+1:]
        i=i+1
    fclear.close()

    fmaxtime.write('#!/bin/bash' + "\n")
    fmaxtime.write('echo "$1" >concore.maxtime\n')
    fmaxtime.write('echo "FROM alpine:3.8" > Dockerfile\n')
    fmaxtime.write('sudo docker build -t docker-concore .\n')
    fmaxtime.write('sudo docker run --name=concore')
    # -v VCZ:/VCZ -v VPZ:/VPZ 
    i=0 #  9/12/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            dockername = sourcecode.rsplit(".", 1)[0] #3/28/21
            writeedges = volswr[i]
            while writeedges.find(":") != -1: 
                fmaxtime.write(' -v ')
                # escape volume paths in Docker run
                vol_path = writeedges.split(":")[0].split("-v ")[1].strip()
                fmaxtime.write(shlex.quote(vol_path)+":/")
                fmaxtime.write(shlex.quote(vol_path))
                writeedges = writeedges[writeedges.find(":")+1:]
        i=i+1
    fmaxtime.write(' docker-concore >/dev/null &\n')
    fmaxtime.write('sleep 3\n')  # 12/6/21
    fmaxtime.write('echo "copying concore.maxtime=$1"\n')
    i=0 #  9/12/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            dockername = sourcecode.rsplit(".", 1)[0] #3/28/21
            writeedges = volswr[i]
            while writeedges.find(":") != -1: 
                fmaxtime.write('sudo docker cp concore.maxtime concore:/')
                # escape destination path in docker cp
                vol_path = writeedges.split(":")[0].split("-v ")[1].strip()
                fmaxtime.write(shlex.quote(vol_path+"/concore.maxtime")+"\n")
                writeedges = writeedges[writeedges.find(":")+1:]
        i=i+1
    fmaxtime.write('sudo docker stop concore \n')
    fmaxtime.write('sudo docker rm concore\n')
    fmaxtime.write('sudo docker rmi docker-concore\n')
    fmaxtime.write('rm Dockerfile\n')
    fmaxtime.write('rm concore.maxtime\n')
    fmaxtime.close()

    fparams.write('#!/bin/bash' + "\n")
    fparams.write('echo "$1" >concore.params\n')
    fparams.write('echo "FROM alpine:3.8" > Dockerfile\n')
    fparams.write('sudo docker build -t docker-concore .\n')
    fparams.write('sudo docker run --name=concore')
    # -v VCZ:/VCZ -v VPZ:/VPZ 
    i=0 #  9/12/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            dockername = sourcecode.rsplit(".", 1)[0] #3/28/21
            writeedges = volswr[i]
            while writeedges.find(":") != -1: 
                fparams.write(' -v ')
                #escape volume paths
                vol_path = writeedges.split(":")[0].split("-v ")[1].strip()
                fparams.write(shlex.quote(vol_path)+":/")
                fparams.write(shlex.quote(vol_path))
                writeedges = writeedges[writeedges.find(":")+1:]
        i=i+1
    fparams.write(' docker-concore >/dev/null &\n')
    fparams.write('sleep 3\n')  # 12/6/21
    fparams.write('echo "copying concore.params=$1"\n')
    i=0 #  9/12/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            dockername = sourcecode.rsplit(".", 1)[0] #3/28/21
            writeedges = volswr[i]
            while writeedges.find(":") != -1: 
                fparams.write('sudo docker cp concore.params concore:/')
                # escape destination path
                vol_path = writeedges.split(":")[0].split("-v ")[1].strip()
                fparams.write(shlex.quote(vol_path+"/concore.params")+"\n")
                writeedges = writeedges[writeedges.find(":")+1:]
        i=i+1
    fparams.write('sudo docker stop concore \n')
    fparams.write('sudo docker rm concore\n')
    fparams.write('sudo docker rmi docker-concore\n')
    fparams.write('rm Dockerfile\n')
    fparams.write('rm concore.params\n')
    fparams.close()

    funlock.write('#!/bin/bash' + "\n")
    funlock.write('echo "FROM alpine:3.8" > Dockerfile\n')
    funlock.write('sudo docker build -t docker-concore .\n')
    funlock.write('sudo docker run --name=concore')
    # -v VCZ:/VCZ -v VPZ:/VPZ 
    i=0 #  9/12/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            dockername = sourcecode.rsplit(".", 1)[0] #3/28/21
            writeedges = volswr[i]
            while writeedges.find(":") != -1: 
                funlock.write(' -v ')
                # escape volume paths
                vol_path = writeedges.split(":")[0].split("-v ")[1].strip()
                funlock.write(shlex.quote(vol_path)+":/")
                funlock.write(shlex.quote(vol_path))
                writeedges = writeedges[writeedges.find(":")+1:]
        i=i+1
    funlock.write(' docker-concore >/dev/null &\n')
    funlock.write('sleep 1\n')
    funlock.write('echo "copying concore.apikey"\n')
    i=0 #  9/12/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            dockername = sourcecode.rsplit(".", 1)[0] #3/28/21
            writeedges = volswr[i]
            while writeedges.find(":") != -1: 
                funlock.write('sudo docker cp ~/concore.apikey concore:/')
                # escape destination path
                vol_path = writeedges.split(":")[0].split("-v ")[1].strip()
                funlock.write(shlex.quote(vol_path+"/concore.apikey")+"\n")
                writeedges = writeedges[writeedges.find(":")+1:]
        i=i+1
    funlock.write('sudo docker stop concore \n')
    funlock.write('sudo docker rm concore\n')
    funlock.write('sudo docker rmi docker-concore\n')
    funlock.write('rm Dockerfile\n')
    funlock.close()

    fdebug.write('#!/bin/bash' + "\n")
    i=0
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0 and sourcecode.find(".")!=-1: #3/28/21
            dockername,langext = sourcecode.rsplit(".", 1)
            # safe_container added to debug line (POSIX)
            safe_container = shlex.quote(containername) 
            safe_image = shlex.quote("docker-" + dockername) # escape docker image name
            fdebug.write(DOCKEREXE+' run -it --name='+safe_container+volswr[i]+volsro[i]+" "+safe_image+"&\n")
        i=i+1
    fdebug.close()
    os.chmod(outdir+"/build",stat.S_IRWXU)
    os.chmod(outdir+"/run",stat.S_IRWXU)
    os.chmod(outdir+"/debug",stat.S_IRWXU)
    os.chmod(outdir+"/stop",stat.S_IRWXU)  
    os.chmod(outdir+"/clear",stat.S_IRWXU) 
    os.chmod(outdir+"/maxtime",stat.S_IRWXU) 
    os.chmod(outdir+"/params",stat.S_IRWXU) 
    os.chmod(outdir+"/unlock",stat.S_IRWXU) 
    quit()

#remaining code deals only with posix or windows

#copy sourcefiles from ./src into corresponding directories
if concoretype=="posix":
    fbuild.write('#!/bin/bash' + "\n")

for node in nodes_dict:
    containername,sourcecode = nodes_dict[node].split(':')
    if len(sourcecode)!=0:
        if sourcecode.find(".")==-1:
            logging.error("cannot pull container "+sourcecode+" with control core type "+concoretype) #3/28/21
            quit()
        dockername,langext = sourcecode.rsplit(".", 1)
        fbuild.write('mkdir '+containername+"\n")
        source_subdir = os.path.dirname(sourcecode).replace("\\", "/")
        if source_subdir:
            if concoretype == "windows":
                fbuild.write("mkdir .\\"+containername+"\\"+source_subdir.replace("/", "\\")+"\n")
            else:
                fbuild.write("mkdir -p ./"+containername+"/"+source_subdir+"\n")
        if concoretype == "windows":
            fbuild.write("copy .\\src\\"+sourcecode+" .\\"+containername+"\\"+sourcecode+"\n")
            if langext == "py":
                fbuild.write("copy .\\src\\concore.py .\\" + containername + "\\concore.py\n")
            elif langext == "cpp":
 # 6/22/21
                fbuild.write("copy .\\src\\concore.hpp .\\" + containername + "\\concore.hpp\n")
            elif langext == "v":
 # 6/25/21
                fbuild.write("copy .\\src\\concore.v .\\" + containername + "\\concore.v\n")
            elif langext == "m":   #  4/2/21
                fbuild.write("copy .\\src\\concore_*.m .\\" + containername + "\\\n")
                fbuild.write("copy .\\src\\import_concore.m .\\" + containername + "\\\n")
            fbuild.write("copy .\\src\\"+dockername+".iport .\\"+containername+"\\concore.iport\n")
            fbuild.write("copy .\\src\\"+dockername+".oport .\\"+containername+"\\concore.oport\n")
            #include data files in here if they exist
            if os.path.isdir(sourcedir+"/"+dockername+".dir"):
                fbuild.write("copy  .\\src\\"+dockername+".dir\\*.* .\\"+containername+"\n")
        else:
            fbuild.write("cp ./src/"+sourcecode+" ./"+containername+"/"+sourcecode+"\n")
            if langext == "py":
                fbuild.write("cp ./src/concore.py ./"+containername+"/concore.py\n")
            elif langext == "cpp":
                fbuild.write("cp ./src/concore.hpp ./"+containername+"/concore.hpp\n")
            elif langext == "v":
                fbuild.write("cp ./src/concore.v ./"+containername+"/concore.v\n")
            elif langext == "m":  # 4/2/21
                fbuild.write("cp ./src/concore_*.m ./"+containername+"/\n")
                fbuild.write("cp ./src/import_concore.m ./"+containername+"/\n")
                fbuild.write("./src/mkcompile "+dockername+" "+containername+"/\n") # 5/27/21
            elif langext == "sh":  # 4/2/28
                fbuild.write("chmod u+x ./"+containername+"/"+sourcecode+"\n")
            fbuild.write("cp ./src/"+dockername+".iport ./"+containername+"/concore.iport\n")
            fbuild.write("cp ./src/"+dockername+".oport ./"+containername+"/concore.oport\n")
            #include data files in here if they exist
            if os.path.isdir(sourcedir+"/"+dockername+".dir"):
                fbuild.write("cp -r ./src/"+dockername+".dir/* ./"+containername+"\n")

 
#make directories equivalent to volumes
for edges in edges_dict:
  fbuild.write("mkdir "+edges+"\n")

#make links for out directories
outcount = len(nodes_dict)*[0]
for edges in edges_dict:
    containername,sourcecode = edges_dict[edges][0].split(':')
    outcount[nodes_num[edges_dict[edges][0]]] += 1
    if len(sourcecode)!=0:
        dockername,langext = sourcecode.rsplit(".", 1)
        fbuild.write('cd '+containername+"\n")
        if concoretype=="windows":
            fbuild.write("mklink /J out"+str(outcount[nodes_num[edges_dict[edges][0]]])+" ..\\"+str(edges)+"\n")
        else:
            fbuild.write("ln -s ../" + str(edges) + ' out'+str(outcount[nodes_num[edges_dict[edges][0]]])+"\n")
        fbuild.write("cd .."+"\n")

#make links for in directories
i=0
for node in nodes_dict:
    containername,sourcecode = nodes_dict[node].split(':')
    if len(sourcecode)!=0:
        dockername,langext = sourcecode.rsplit(".", 1)
        fbuild.write('cd '+containername+"\n")
        for pair in indir[i]:
            volname,dirname = pair.split(':/')
            if concoretype=="windows":
                fbuild.write("mklink /J "+dirname+" ..\\"+volname+"\n")
            else:
                fbuild.write("ln -s ../"+volname+" "+dirname+"\n")
        fbuild.write('cd ..'+"\n") 
    i=i+1

#start running source in associated dirs (run and debug scripts)
if concoretype=="posix":
    fdebug.write('#!/bin/bash' + "\n")
    frun.write('#!/bin/bash' + "\n")


i=0
for node in nodes_dict:
  containername,sourcecode = nodes_dict[node].split(':')
  if len(sourcecode)!=0:
      dockername,langext = sourcecode.rsplit(".", 1)
      if not (langext in ["py","m","sh","cpp","v"]): # 6/22/21
          logging.error(f"Extension .{langext} is unsupported")
          quit()
      if concoretype=="windows":
          # manual double quoting for Windows + Input validation above prevents breakout
          q_container = f'"{containername}"'
          q_source = f'"{sourcecode}"'

          if langext=="py":
              frun.write('start /B /D '+q_container+" "+PYTHONWIN+" "+q_source+" >"+q_container+"\\concoreout.txt\n")
              fdebug.write('start /D '+q_container+" cmd /K "+PYTHONWIN+" "+q_source+"\n")
          elif langext=="cpp":  #6/25/21
              frun.write('cd '+q_container+'\n')
              frun.write(CPPWIN+' '+q_source+'\n')
              frun.write('cd ..\n')
              frun.write('start /B /D '+q_container+' cmd /c a >'+q_container+'\\concoreout.txt\n')
              #frun.write('start /B /D '+containername+' "'+CPPWIN+' '+sourcecode+'|a >'+containername+'\\concoreout.txt"\n')
              fdebug.write('cd '+q_container+'\n')
              fdebug.write(CPPWIN+' '+q_source+'\n')
              fdebug.write('cd ..\n')
              fdebug.write('start /D '+q_container+' cmd /K a\n')
              #fdebug.write('start /D '+containername+' cmd /K "'+CPPWIN+' '+sourcecode+'|a"\n')
          elif langext=="v":  #6/25/21
              frun.write('cd '+q_container+'\n')
              frun.write(VWIN+' '+q_source+'\n')
              frun.write('cd ..\n')
              frun.write('start /B /D '+q_container+' cmd /c vvp a.out >'+q_container+'\\concoreout.txt\n')
              fdebug.write('cd '+q_container+'\n')
              fdebug.write(VWIN+' '+q_source+'\n')
              fdebug.write('cd ..\n')
              fdebug.write('start /D '+q_container+' cmd /K vvp a.out\n')
              #fdebug.write('start /D '+containername+' cmd /K "'+CPPWIN+' '+sourcecode+'|a"\n')
          elif langext=="m":  #3/23/21
              # Use q_source in Windows commands to ensure quoting consistency
              if M_IS_OCTAVE:   
                  frun.write('start /B /D '+q_container+" "+OCTAVEWIN+' -qf --eval "run('+q_source+')"'+" >"+q_container+"\\concoreout.txt\n")
                  fdebug.write('start /D '+q_container+" cmd /K " +OCTAVEWIN+' -qf --eval "run('+q_source+')"'+"\n")
              else:  #  4/2/21
                  frun.write('start /B /D '+q_container+" "+MATLABWIN+' -batch "run('+q_source+')"'+" >"+q_container+"\\concoreout.txt\n")
                  fdebug.write('start /D '+q_container+" cmd /K " +MATLABWIN+' -batch "run('+q_source+')"'+"\n")
      else:
            #use shlex.quote for POSIX systems
            safe_container = shlex.quote(containername)
            safe_source = shlex.quote(sourcecode)

            if langext == "py":
                frun.write('(cd ' + safe_container + '; ' + PYTHONEXE + ' ' + safe_source + ' >concoreout.txt & echo $! >concorepid) &\n')
                if ubuntu:
                    fdebug.write('concorewd="$(pwd)"\n')
                    # quote the directory path inside the inner bash command
                    fdebug.write('xterm -e bash -c "cd \\"$concorewd/' + safe_container + '\\"; ' + PYTHONEXE + ' ' + safe_source + '; bash" &\n')
                else:
                    fdebug.write('concorewd="$(pwd)"\n')
                    fdebug.write('osascript -e "tell application \\"Terminal\\" to do script \\"cd \\\\\\"$concorewd/' + safe_container + '\\\\\\"; ' + PYTHONEXE + ' ' + safe_source + '\\"" \n')

            elif langext == "cpp":  # 6/22/21
                frun.write('(cd ' + safe_container + '; ' + CPPEXE + ' ' + safe_source + '; ./a.out >concoreout.txt & echo $! >concorepid) &\n')
                if ubuntu:
                    fdebug.write('concorewd="$(pwd)"\n')
                    fdebug.write('xterm -e bash -c "cd \\"$concorewd/' + safe_container + '\\"; ' + CPPEXE + ' ' + safe_source + '; ./a.out; bash" &\n')
                else:
                    fdebug.write('concorewd="$(pwd)"\n')
                    fdebug.write('osascript -e "tell application \\"Terminal\\" to do script \\"cd \\\\\\"$concorewd/' + safe_container + '\\\\\\"; ' + CPPEXE + ' ' + safe_source + '; ./a.out\\"" \n')

            elif langext == "v":    # 6/25/21
                frun.write('(cd ' + safe_container + '; ' + VEXE + ' ' + safe_source + '; ./a.out >concoreout.txt & echo $! >concorepid) &\n')
                if ubuntu:
                    fdebug.write('concorewd="$(pwd)"\n')
                    fdebug.write('xterm -e bash -c "cd \\"$concorewd/' + safe_container + '\\"; ' + VEXE + ' ' + safe_source + '; ./a.out; bash" &\n')
                else:
                    fdebug.write('concorewd="$(pwd)"\n')
                    fdebug.write('osascript -e "tell application \\"Terminal\\" to do script \\"cd \\\\\\"$concorewd/' + safe_container + '\\\\\\"; ' + VEXE + ' ' + safe_source + '; vvp a.out\\"" \n')

            elif langext == "sh":   # 5/19/21
                # FIX: Escape MCRPATH to prevent shell injection
                safe_mcr = shlex.quote(MCRPATH)
                frun.write('(cd ' + safe_container + '; ./' + safe_source + ' ' + safe_mcr + ' >concoreout.txt & echo $! >concorepid) &\n')
                if ubuntu:
                    fdebug.write('concorewd="$(pwd)"\n')
                    fdebug.write('xterm -e bash -c "cd \\"$concorewd/' + safe_container + '\\"; ./' + safe_source + ' ' + safe_mcr + '; bash" &\n')
                else:
                    fdebug.write('concorewd="$(pwd)"\n')
                    fdebug.write('osascript -e "tell application \\"Terminal\\" to do script \\"cd \\\\\\"$concorewd/' + safe_container + '\\\\\\"; ./' + safe_source + ' ' + safe_mcr + '\\"" \n')

            elif langext == "m":    #3/23/21
                # FIX: Verify filename safety for MATLAB to prevent injection in run()
                # MATLAB/Octave run('filename') is vulnerable if filename contains quotes or metachars.
                if not re.match(r'^[A-Za-z0-9_./\-]+$', sourcecode):
                    raise ValueError(f"Invalid MATLAB/Octave source file name: {sourcecode!r}")

                # construct safe eval command
                safe_eval_cmd = shlex.quote(f"run('{sourcecode}')")
                if M_IS_OCTAVE:
                    frun.write('(cd ' + safe_container + '; ' + OCTAVEEXE + ' -qf --eval ' + safe_eval_cmd + ' >concoreout.txt & echo $! >concorepid) &\n')
                    if ubuntu:
                        fdebug.write('concorewd="$(pwd)"\n')
                        fdebug.write('xterm -e bash -c "cd \\"$concorewd/' + safe_container + '\\"; ' + OCTAVEEXE + ' -qf --eval ' + safe_eval_cmd + '; bash" &\n')
                    else:
                        fdebug.write('concorewd="$(pwd)"\n')
                        #osascript quoting is very complex; minimal safe_container applied
                        fdebug.write('osascript -e "tell application \\"Terminal\\" to do script \\"cd \\\\\\"$concorewd/' + safe_container + '\\\\\\"; ' + OCTAVEEXE + ' -qf --eval run(\\\\\\\'' + sourcecode + '\\\\\\\')\\"" \n')
                else:
                    frun.write('(cd ' + safe_container + '; ' + MATLABEXE + ' -batch ' + safe_eval_cmd + ' >concoreout.txt & echo $! >concorepid) &\n')
                    if ubuntu:
                        fdebug.write('concorewd="$(pwd)"\n')
                        fdebug.write('xterm -e bash -c "cd \\"$concorewd/' + safe_container + '\\"; ' + MATLABEXE + ' -batch ' + safe_eval_cmd + '; bash" &\n')
                    else:
                        fdebug.write('concorewd="$(pwd)"\n')
                        fdebug.write('osascript -e "tell application \\"Terminal\\" to do script \\"cd \\\\\\"$concorewd/' + safe_container + '\\\\\\"; ' + MATLABEXE + ' -batch run(\\\\\\\'' + sourcecode + '\\\\\\\')\\"" \n')
if concoretype=="posix":
    fstop.write('#!/bin/bash' + "\n")
i=0 #  3/30/21
for node in nodes_dict:
    containername,sourcecode = nodes_dict[node].split(':')
    if len(sourcecode)!=0:
        dockername = sourcecode.rsplit(".", 1)[0] # 3/28/21
        if concoretype=="windows":
            q_container = f'"{containername}"'
            fstop.write('cmd /C '+q_container+"\\concorekill\n")
            fstop.write('del '+q_container+"\\concorekill.bat\n")
        else:
            safe_pidfile = shlex.quote(f"{containername}/concorepid")
            fstop.write('kill -9 `cat '+safe_pidfile+'`\n')
            fstop.write('rm '+safe_pidfile+'\n')
    i=i+1
fstop.close()

if concoretype=="posix":
    fclear.write('#!/bin/bash' + "\n")
i=0 #  9/13/21
for node in nodes_dict:
    containername,sourcecode = nodes_dict[node].split(':')
    if len(sourcecode)!=0:
        dockername = sourcecode.rsplit(".", 1)[0] #3/28/21
        writeedges = volswr[i]
        while writeedges.find(":") != -1: 
            path_part = writeedges.split(":")[0].split("-v")[1].strip()
            if concoretype=="windows":
                fclear.write('del /Q "' + path_part + '\\*"\n')
            else:
                # FIX: Safer wildcard removal. 
                # Avoid quoting the wildcard itself ('path/*'). Instead cd into directory and remove contents.
                fclear.write(f'cd {shlex.quote(path_part)} && rm -f *\n')
            writeedges = writeedges[writeedges.find(":")+1:]
    i=i+1
fclear.close()

if concoretype=="posix":
    fmaxtime.write('#!/bin/bash' + "\n")
i=0 #  9/12/21
for node in nodes_dict:
    containername,sourcecode = nodes_dict[node].split(':')
    if len(sourcecode)!=0:
        dockername = sourcecode.rsplit(".", 1)[0] #3/28/21
        writeedges = volswr[i]
        while writeedges.find(":") != -1: 
            path_part = writeedges.split(":")[0].split("-v")[1].strip()
            if concoretype=="windows":
                fmaxtime.write('echo %1 >"' + path_part + '\\concore.maxtime"\n')
            else:
                fmaxtime.write('echo "$1" >' + shlex.quote(path_part + "/concore.maxtime") + '\n')
            writeedges = writeedges[writeedges.find(":")+1:]
    i=i+1
fmaxtime.close()

if concoretype=="posix":
    fparams.write('#!/bin/bash' + "\n")
i=0 #  9/18/22
for node in nodes_dict:
    containername,sourcecode = nodes_dict[node].split(':')
    if len(sourcecode)!=0:
        dockername = sourcecode.rsplit(".", 1)[0] #3/28/21
        writeedges = volswr[i]
        while writeedges.find(":") != -1: 
            path_part = writeedges.split(":")[0].split("-v")[1].strip()
            if concoretype=="windows":
                fparams.write('echo %1 >"' + path_part + '\\concore.params"\n')
            else:
                fparams.write('echo "$1" >' + shlex.quote(path_part + "/concore.params") + '\n')
            writeedges = writeedges[writeedges.find(":")+1:]
    i=i+1
fparams.close()

if concoretype=="posix":
    funlock.write('#!/bin/bash' + "\n")
i=0 #  9/12/21
for node in nodes_dict:
    containername,sourcecode = nodes_dict[node].split(':')
    if len(sourcecode)!=0:
        dockername = sourcecode.rsplit(".", 1)[0] #3/28/21
        writeedges = volswr[i]
        while writeedges.find(":") != -1: 
            path_part = writeedges.split(":")[0].split("-v")[1].strip()
            if concoretype=="windows":
                funlock.write('copy %HOMEDRIVE%%HOMEPATH%\\concore.apikey "' + path_part + '\\concore.apikey"\n')
            else:
                funlock.write('cp ~/concore.apikey ' + shlex.quote(path_part + "/concore.apikey") + '\n')
            writeedges = writeedges[writeedges.find(":")+1:]
    i=i+1
funlock.close()


frun.close()
fbuild.close()
fdebug.close()
if concoretype != "windows":
    os.chmod(outdir+"/build",stat.S_IRWXU)
    os.chmod(outdir+"/run",stat.S_IRWXU)
    os.chmod(outdir+"/debug",stat.S_IRWXU)
    os.chmod(outdir+"/stop",stat.S_IRWXU)  
    os.chmod(outdir+"/clear",stat.S_IRWXU) 
    os.chmod(outdir+"/maxtime",stat.S_IRWXU) 
    os.chmod(outdir+"/params",stat.S_IRWXU) 
    os.chmod(outdir+"/unlock",stat.S_IRWXU)
