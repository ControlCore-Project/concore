from bs4 import BeautifulSoup
import logging
import re
import sys
import os
import shutil
import stat

MKCONCORE_VER = "22-09-18"

GRAPHML_FILE = sys.argv[1]
TRIMMED_LOGS = True
CONCOREPATH = "."
CPPWIN    = "g++"        #Windows C++  6/22/21
CPPEXE    = "g++"        #Ubuntu/macOS C++  6/22/21
VWIN      = "iverilog"   #Windows verilog  6/25/21
VEXE      = "iverilog"   #Ubuntu/macOS verilog  6/25/21
CPPEXE    = "g++"        #Ubuntu/macOS C++  6/22/21
PYTHONEXE = "python3"    #Ubuntu/macOS python 3
PYTHONWIN = "python"         #Windows python 3
MATLABEXE = "matlab"     #Ubuntu/macOS matlab 
MATLABWIN = "matlab"     #Windows matlab 
OCTAVEEXE = "octave"     #Ubuntu/macOS octave 
OCTAVEWIN = "octave"     #Windows octave 
M_IS_OCTAVE = False       #treat .m as octave
MCRPATH  = "~/MATLAB/R2021a" #path to local Ubunta Matlab Compiler Runtime
DOCKEREXE = "sudo docker"#assume simple docker install
DOCKEREPO = "markgarnold"#where pulls come from 3/28/21
INDIRNAME = ":/in"
OUTDIRNAME = ":/out"


if os.path.exists(CONCOREPATH+"/concore.octave"):
    M_IS_OCTAVE = True       #treat .m as octave 9/27/21

if os.path.exists(CONCOREPATH+"/concore.mcr"): # 11/12/21
    MCRPATH = open(CONCOREPATH+"/concore.mcr", "r").readline().strip() #path to local Ubunta Matlab Compiler Runtime
    
if os.path.exists(CONCOREPATH+"/concore.sudo"): # 12/04/21
    DOCKEREXE = open(CONCOREPATH+"/concore.sudo", "r").readline().strip() #to omit sudo in docker

if os.path.exists(CONCOREPATH+"/concore.repo"): # 12/04/21
    DOCKEREPO = open(CONCOREPATH+"/concore.repo", "r").readline().strip() #docker id for repo


prefixedgenode = ""
sourcedir = sys.argv[2]
apikeyindex = sourcedir.find('_')
apikey = sourcedir[apikeyindex:-1]
outdirpre = sys.argv[3]
outdir = outdirpre + apikey
if not os.path.isdir(sourcedir):
    print(sourcedir+" does not exist")
    quit()

if len(sys.argv) < 4:
    print("usage: py mkconcore.py file.graphml sourcedir outdir [type]")
    print(" type must be posix (macos or ubuntu), windows, or docker")
    quit()
elif len(sys.argv) == 4:
    prefixedgenode = outdir+"_" #nodes and edges prefixed with outdir_ only in case no type specified 3/24/21
    concoretype = "docker"
else:
    concoretype = sys.argv[4]
    if not (concoretype in ["posix","windows","docker","macos","ubuntu"]):
        print(" type must be posix (macos or ubuntu), windows, or docker")
        quit()
ubuntu = False #6/24/21
if concoretype == "ubuntu":
    concoretype = "posix"
    ubuntu = True
if concoretype == "macos":
    concoretype = "posix"

if os.path.exists(outdir):
    print(outdir+" already exists")
    print("if intended, remove or rename "+outdir+" first")
    quit()

currentdir = os.getcwd()
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

os.mkdir("src")
os.chdir("..")
        
print("mkconcore "+MKCONCORE_VER)
print("concore path:      "+CONCOREPATH)
print("graphml input:     "+GRAPHML_FILE)
print("source directory:  "+sourcedir)
print("output directory:  "+outdir)
print("control core type: "+concoretype)
print("treat .m as octave:"+str(M_IS_OCTAVE))
print("MCR path:          "+MCRPATH)
print("Docker repository: "+DOCKEREPO)

# Output in a preferred format.
if TRIMMED_LOGS:
    logging.basicConfig(level=logging.INFO, format='%(message)s')
else:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

f = open(GRAPHML_FILE, "r")
text_str = f.read()

soup = BeautifulSoup(text_str, 'xml')

edges_text = soup.find_all('edge')
nodes_text = soup.find_all('node')

# Store the edges and nodes in a dictionary
edges_dict = dict()
nodes_dict = dict()

for node in nodes_text:
    node_key = node.get_text()
    length = len(node.find_all('data'))
    for i in range(length):
        try:
            data = node.find_all('data')[i]
            node_label = prefixedgenode + data.find('y:NodeLabel').text #3/23/21
            nodes_dict[node['id']] = re.sub(r'(\s+|\n)', ' ', node_label)
        except IndexError:
            logging.debug('IndexError: A node with no valid properties encountered and ignored')
        except AttributeError:
            logging.debug('AttributeError: A node with no valid properties encountered and ignored')

for edge in edges_text:
    length = len(edge.find_all('data'))
    for i in range(length):
        try:
            data = edge.find_all('data')[i]
            edge_label = prefixedgenode + data.find('y:EdgeLabel').text # 3/23/21
            if edges_dict.get(edge_label) != None:
                targets = edges_dict[edge_label][1]
            else:
                targets = []
            targets.append(nodes_dict[edge['target']])
            edges_dict[edge_label] = [nodes_dict[edge['source']], targets]
        except IndexError:
            logging.debug('An edge with no valid properties encountered and ignored')
        except AttributeError:
            logging.debug('AttributeError: An edge with no valid properties encountered and ignored')

# Print the edges_dict    
#logging.info(edges_dict)

############## Mark's Docker
import numpy as np

i=0
nodes_num=dict()
for node in nodes_dict:
  nodes_num[nodes_dict[node]] = i
  i=i+1

m=np.zeros((len(nodes_dict),len(nodes_dict)))
for edges in edges_dict:
   for dest in (edges_dict[edges])[1]:
      m[nodes_num[edges_dict[edges][0]]][nodes_num[dest]] = 1

mp = np.eye(len(nodes_dict))
ms = np.zeros((len(nodes_dict),len(nodes_dict)))

for i in range(0,len(nodes_dict)):
  mp = mp@m
  ms += mp

if (ms == 0).any():
  print("not all nodes reachable")

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

#copy sourcedir into ./src
for node in nodes_dict:
    containername,sourcecode = nodes_dict[node].split(':')
    if len(sourcecode)!=0 and sourcecode.find(".")!=-1: #3/28/21
        dockername,langext = sourcecode.split(".")
        try:
            fsource = open(sourcedir+"/"+sourcecode)
        except:
            print(sourcecode+" does not exist in "+sourcedir)
            quit()
        with open(outdir+"/src/"+sourcecode,"w") as fcopy:
            fcopy.write(fsource.read())
        fsource.close()
        if concoretype == "docker": # 3/30/21
            try:
                fsource = open(sourcedir+"/Dockerfile."+dockername)
                with open(outdir+"/src/Dockerfile."+dockername,"w") as fcopy:
                    fcopy.write(fsource.read())
                print(" Using custom Dockerfile for "+dockername)
            except:
                print(" Using default Dockerfile for "+dockername)
            fsource.close()
        if os.path.isdir(sourcedir+"/"+dockername+".dir"):
            shutil.copytree(sourcedir+"/"+dockername+".dir",outdir+"/src/"+dockername+".dir")
    
#copy proper concore.py into /src
try:
    if concoretype=="docker":
        fsource = open(CONCOREPATH+"/concoredocker.py")
    else:
        fsource = open(CONCOREPATH+"/concore.py")
except:
    print(CONCOREPATH+" is not correct path to concore")
    quit()
with open(outdir+"/src/concore.py","w") as fcopy:
    fcopy.write(fsource.read())
fsource.close()

#copy proper concore.hpp into /src 6/22/21
try:
    if concoretype=="docker":
        fsource = open(CONCOREPATH+"/concoredocker.hpp")
    else:
        fsource = open(CONCOREPATH+"/concore.hpp")
except:
    print(CONCOREPATH+" is not correct path to concore")
    quit()
with open(outdir+"/src/concore.hpp","w") as fcopy:
    fcopy.write(fsource.read())
fsource.close()

#copy proper concore.v into /src 6/25/21
try:
    if concoretype=="docker":
        fsource = open(CONCOREPATH+"/concoredocker.v")
    else:
        fsource = open(CONCOREPATH+"/concore.v")
except:
    print(CONCOREPATH+" is not correct path to concore")
    quit()
with open(outdir+"/src/concore.v","w") as fcopy:
    fcopy.write(fsource.read())
fsource.close()

#copy mkcompile into /src  5/27/21
try:
    fsource = open(CONCOREPATH+"/mkcompile")
except:
    print(CONCOREPATH+" is not correct path to concore")
    quit()
with open(outdir+"/src/mkcompile","w") as fcopy:
    fcopy.write(fsource.read())
fsource.close()
os.chmod(outdir+"/src/mkcompile",stat.S_IRWXU)

#copy concore*.m into /src  4/2/21
try: #maxtime in matlab 11/22/21
    fsource = open(CONCOREPATH+"/concore_default_maxtime.m")
except:
    print(CONCOREPATH+" is not correct path to concore")
    quit()
with open(outdir+"/src/concore_default_maxtime.m","w") as fcopy:
    fcopy.write(fsource.read())
fsource.close()
try:
    fsource = open(CONCOREPATH+"/concore_unchanged.m")
except:
    print(CONCOREPATH+" is not correct path to concore")
    quit()
with open(outdir+"/src/concore_unchanged.m","w") as fcopy:
    fcopy.write(fsource.read())
fsource.close()
try:
    fsource = open(CONCOREPATH+"/concore_read.m")
except:
    print(CONCOREPATH+" is not correct path to concore")
    quit()
with open(outdir+"/src/concore_read.m","w") as fcopy:
    fcopy.write(fsource.read())
fsource.close()
try:
    fsource = open(CONCOREPATH+"/concore_write.m")
except:
    print(CONCOREPATH+" is not correct path to concore")
    quit()
with open(outdir+"/src/concore_write.m","w") as fcopy:
    fcopy.write(fsource.read())
fsource.close()
try: #4/9/21
    fsource = open(CONCOREPATH+"/concore_initval.m")
except:
    print(CONCOREPATH+" is not correct path to concore")
    quit()
with open(outdir+"/src/concore_initval.m","w") as fcopy:
    fcopy.write(fsource.read())
fsource.close()
try: #11/19/21
    fsource = open(CONCOREPATH+"/concore_iport.m")
except:
    print(CONCOREPATH+" is not correct path to concore")
    quit()
with open(outdir+"/src/concore_iport.m","w") as fcopy:
    fcopy.write(fsource.read())
fsource.close()
try: #11/19/21
    fsource = open(CONCOREPATH+"/concore_oport.m")
except:
    print(CONCOREPATH+" is not correct path to concore")
    quit()
with open(outdir+"/src/concore_oport.m","w") as fcopy:
    fcopy.write(fsource.read())
fsource.close()
try: # 4/4/21
    if concoretype=="docker":
        fsource = open(CONCOREPATH+"/import_concoredocker.m")
    else:
        fsource = open(CONCOREPATH+"/import_concore.m")
except:
    print(CONCOREPATH+" is not correct path to concore")
    quit()
with open(outdir+"/src/import_concore.m","w") as fcopy:
    fcopy.write(fsource.read())
fsource.close()


#generate input portmap file
i=0
for node in nodes_dict:
    containername,sourcecode = nodes_dict[node].split(':')
    iportmap_dict = dict()
    for pair in indir[i]:
        volname,portnum = pair.split(INDIRNAME)
        iportmap_dict[volname] = int(portnum) 
    if len(sourcecode)!=0 and sourcecode.find(".")!=-1: #3/28/21
        dockername,langext = sourcecode.split(".")
        if os.path.exists(outdir+"/src/"+dockername+".iport"):
            print("warning: "+dockername+" has multiple instantiations; iport/oport may be invalid")
        with open(outdir+"/src/"+dockername+".iport", "w") as fport:
          if prefixedgenode == "": # 5/18/21
            fport.write(str(iportmap_dict)) 
          else:
            fport.write(str(iportmap_dict).replace("'"+prefixedgenode,"'")) 
    i=i+1

#generate output portmap file
outcount = len(nodes_dict)*[0]
#wrong, this aliases single dict for all elements: oportmap = len(nodes_dict)*[dict()]
#instead, need to use a loop to initialize:
oportmap_dict = []
for node in nodes_dict:
    oportmap_dict += [dict()]
for edges in edges_dict:
    containername,sourcecode = edges_dict[edges][0].split(':')
    outcount[nodes_num[edges_dict[edges][0]]] += 1
    oportmap_dict[nodes_num[edges_dict[edges][0]]][edges] = outcount[nodes_num[edges_dict[edges][0]]]
i=0
for node in nodes_dict:
    containername,sourcecode = nodes_dict[node].split(':')
    if len(sourcecode)!=0 and sourcecode.find(".")!=-1: #3/28/21
        dockername,langext = sourcecode.split(".")
        with open(outdir+"/src/"+dockername+".oport", "w") as fport:
          if prefixedgenode == "": # 5/18/21
            fport.write(str(oportmap_dict[i])) 
          else:
            fport.write(str(oportmap_dict[i]).replace("'"+prefixedgenode,"'")) 
    i=i+1

#if docker, make docker-dirs, generate build, run, stop, clear scripts and quit
if (concoretype=="docker"):
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0 and sourcecode.find(".")!=-1: #3/28/21
            dockername,langext = sourcecode.split(".")
            if not os.path.exists(outdir+"/src/Dockerfile."+dockername): # 3/30/21
                try:
                    if langext=="py":
                        fsource = open(CONCOREPATH+"/Dockerfile.py")
                        print("assuming .py extension for Dockerfile")
                    elif langext == "cpp":  # 6/22/21
                        fsource = open(CONCOREPATH+"/Dockerfile.cpp")
                        print("assuming .cpp extension for Dockerfile")
                    elif langext == "v":  # 6/26/21
                        fsource = open(CONCOREPATH+"/Dockerfile.v")
                        print("assuming .v extension for Dockerfile")
                    elif langext == "sh":  # 5/19/21
                        fsource = open(CONCOREPATH+"/Dockerfile.sh")
                        print("assuming .sh extension for Dockerfile")
                    else:
                        print("assuming .m extension for Dockerfile")
                        fsource = open(CONCOREPATH+"/Dockerfile.m")
                except:
                    print(CONCOREPATH+" is not correct path to concore")
                    quit()
                with open(outdir+"/src/Dockerfile."+dockername,"w") as fcopy:
                    fcopy.write(fsource.read())
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
                fsource.close() 

    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0 and sourcecode.find(".")!=-1: #3/28/21
            dockername,langext = sourcecode.split(".")
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

    i=0
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            if sourcecode.find(".")==-1:
                print(DOCKEREXE+' run --name='+containername+volswr[i]+volsro[i]+" "+DOCKEREPO+"/docker-"+sourcecode)
                frun.write(DOCKEREXE+' run --name='+containername+volswr[i]+volsro[i]+" "+DOCKEREPO+"/docker-"+sourcecode+"&\n")
            else:    
                dockername,langext = sourcecode.split(".")
                print(DOCKEREXE+' run --name='+containername+volswr[i]+volsro[i]+" docker-"+dockername)
                frun.write(DOCKEREXE+' run --name='+containername+volswr[i]+volsro[i]+" docker-"+dockername+"&\n")
                #if langext != "m": #3/27/21
                #    print(DOCKEREXE+' run --name='+containername+volswr[i]+volsro[i]+" docker-"+dockername)
                #    frun.write(DOCKEREXE+' run --name='+containername+volswr[i]+volsro[i]+" docker-"+dockername+"&\n")
                #else:
                #    print(DOCKEREXE+' run --name='+containername+volswr[i]+volsro[i]+" docker-"+dockername+' octave  -qf --eval "run('+"'"+sourcecode+"'"+')"'+"&\n")
                #    frun.write(DOCKEREXE+' run --name='+containername+volswr[i]+volsro[i]+" docker-"+dockername+' octave  -qf --eval "run('+"'"+sourcecode+"'"+')"'+"&\n")
        i=i+1
    frun.close()

    i=0 #  3/27/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            #dockername,langext = sourcecode.split(".")
            dockername = sourcecode.split(".")[0] # 3/28/21
            fstop.write(DOCKEREXE+' stop '+containername+"\n")
            fstop.write(DOCKEREXE+' rm '+containername+"\n")
        i=i+1
    fstop.close()

    i=0 #  9/13/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            dockername = sourcecode.split(".")[0] #3/28/21
            writeedges = volswr[i]
            while writeedges.find(":") != -1: 
                fclear.write(DOCKEREXE+' volume rm ' +writeedges.split(":")[0].split("-v")[1]+"\n")
                writeedges = writeedges[writeedges.find(":")+1:]
        i=i+1
    fclear.close()

    fmaxtime.write('echo "$1" >concore.maxtime\n')
    fmaxtime.write('echo "FROM alpine:3.8" > Dockerfile\n')
    fmaxtime.write('sudo docker build -t docker-concore .\n')
    fmaxtime.write('sudo docker run --name=concore')
    # -v VCZ:/VCZ -v VPZ:/VPZ 
    i=0 #  9/12/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            dockername = sourcecode.split(".")[0] #3/28/21
            writeedges = volswr[i]
            while writeedges.find(":") != -1: 
                fmaxtime.write(' -v ')
                fmaxtime.write(writeedges.split(":")[0].split("-v ")[1]+":/")
                fmaxtime.write(writeedges.split(":")[0].split("-v ")[1])
                writeedges = writeedges[writeedges.find(":")+1:]
        i=i+1
    fmaxtime.write(' docker-concore >/dev/null &\n')
    fmaxtime.write('sleep 3\n')  # 12/6/21
    fmaxtime.write('echo "copying concore.maxtime=$1"\n')
    i=0 #  9/12/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            dockername = sourcecode.split(".")[0] #3/28/21
            writeedges = volswr[i]
            while writeedges.find(":") != -1: 
                fmaxtime.write('sudo docker cp concore.maxtime concore:/')
                fmaxtime.write(writeedges.split(":")[0].split("-v ")[1]+"/concore.maxtime\n")
                writeedges = writeedges[writeedges.find(":")+1:]
        i=i+1
    fmaxtime.write('sudo docker stop concore \n')
    fmaxtime.write('sudo docker rm concore\n')
    fmaxtime.write('sudo docker rmi docker-concore\n')
    fmaxtime.write('rm Dockerfile\n')
    fmaxtime.write('rm concore.maxtime\n')
    fmaxtime.close()

    fparams.write('echo "$1" >concore.params\n')
    fparams.write('echo "FROM alpine:3.8" > Dockerfile\n')
    fparams.write('sudo docker build -t docker-concore .\n')
    fparams.write('sudo docker run --name=concore')
    # -v VCZ:/VCZ -v VPZ:/VPZ 
    i=0 #  9/12/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            dockername = sourcecode.split(".")[0] #3/28/21
            writeedges = volswr[i]
            while writeedges.find(":") != -1: 
                fparams.write(' -v ')
                fparams.write(writeedges.split(":")[0].split("-v ")[1]+":/")
                fparams.write(writeedges.split(":")[0].split("-v ")[1])
                writeedges = writeedges[writeedges.find(":")+1:]
        i=i+1
    fparams.write(' docker-concore >/dev/null &\n')
    fparams.write('sleep 3\n')  # 12/6/21
    fparams.write('echo "copying concore.params=$1"\n')
    i=0 #  9/12/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            dockername = sourcecode.split(".")[0] #3/28/21
            writeedges = volswr[i]
            while writeedges.find(":") != -1: 
                fparams.write('sudo docker cp concore.params concore:/')
                fparams.write(writeedges.split(":")[0].split("-v ")[1]+"/concore.params\n")
                writeedges = writeedges[writeedges.find(":")+1:]
        i=i+1
    fparams.write('sudo docker stop concore \n')
    fparams.write('sudo docker rm concore\n')
    fparams.write('sudo docker rmi docker-concore\n')
    fparams.write('rm Dockerfile\n')
    fparams.write('rm concore.params\n')
    fparams.close()


    funlock.write('echo "FROM alpine:3.8" > Dockerfile\n')
    funlock.write('sudo docker build -t docker-concore .\n')
    funlock.write('sudo docker run --name=concore')
    # -v VCZ:/VCZ -v VPZ:/VPZ 
    i=0 #  9/12/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            dockername = sourcecode.split(".")[0] #3/28/21
            writeedges = volswr[i]
            while writeedges.find(":") != -1: 
                funlock.write(' -v ')
                funlock.write(writeedges.split(":")[0].split("-v ")[1]+":/")
                funlock.write(writeedges.split(":")[0].split("-v ")[1])
                writeedges = writeedges[writeedges.find(":")+1:]
        i=i+1
    funlock.write(' docker-concore >/dev/null &\n')
    funlock.write('sleep 1\n')
    funlock.write('echo "copying concore.apikey"\n')
    i=0 #  9/12/21
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0:
            dockername = sourcecode.split(".")[0] #3/28/21
            writeedges = volswr[i]
            while writeedges.find(":") != -1: 
                funlock.write('sudo docker cp ~/concore.apikey concore:/')
                funlock.write(writeedges.split(":")[0].split("-v ")[1]+"/concore.apikey\n")
                writeedges = writeedges[writeedges.find(":")+1:]
        i=i+1
    funlock.write('sudo docker stop concore \n')
    funlock.write('sudo docker rm concore\n')
    funlock.write('sudo docker rmi docker-concore\n')
    funlock.write('rm Dockerfile\n')
    funlock.close()


    i=0
    for node in nodes_dict:
        containername,sourcecode = nodes_dict[node].split(':')
        if len(sourcecode)!=0 and sourcecode.find(".")!=-1: #3/28/21
            dockername,langext = sourcecode.split(".")
            fdebug.write(DOCKEREXE+' run -it --name='+containername+volswr[i]+volsro[i]+" docker-"+dockername+"&\n")
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
            print("cannot pull container "+sourcecode+" with control core type "+concoretype) #3/28/21
            quit()
        dockername,langext = sourcecode.split(".")
        fbuild.write('mkdir '+containername+"\n")
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
  #print("mkdir "+edges)
  fbuild.write("mkdir "+edges+"\n")

#make links for out directories
outcount = len(nodes_dict)*[0]
for edges in edges_dict:
    containername,sourcecode = edges_dict[edges][0].split(':')
    outcount[nodes_num[edges_dict[edges][0]]] += 1
    if len(sourcecode)!=0:
        dockername,langext = sourcecode.split(".")
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
        dockername,langext = sourcecode.split(".")
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
      dockername,langext = sourcecode.split(".")
      if not (langext in ["py","m","sh","cpp","v"]): # 6/22/21
          print("."+langext+" not supported (Yet)")
          quit()
      if concoretype=="windows":
          if langext=="py":
              frun.write('start /B /D '+containername+" "+PYTHONWIN+" "+sourcecode+" >"+containername+"\\concoreout.txt\n")
              fdebug.write('start /D '+containername+" cmd /K "+PYTHONWIN+" "+sourcecode+"\n")
          elif langext=="cpp":  #6/25/21
              frun.write('cd '+containername+'\n')
              frun.write(CPPWIN+' '+sourcecode+'\n')
              frun.write('cd ..\n')
              frun.write('start /B /D '+containername+' cmd /c a >'+containername+'\\concoreout.txt\n')
              #frun.write('start /B /D '+containername+' "'+CPPWIN+' '+sourcecode+'|a >'+containername+'\\concoreout.txt"\n')
              fdebug.write('cd '+containername+'\n')
              fdebug.write(CPPWIN+' '+sourcecode+'\n')
              fdebug.write('cd ..\n')
              fdebug.write('start /D '+containername+' cmd /K a\n')
              #fdebug.write('start /D '+containername+' cmd /K "'+CPPWIN+' '+sourcecode+'|a"\n')
          elif langext=="v":  #6/25/21
              frun.write('cd '+containername+'\n')
              frun.write(VWIN+' '+sourcecode+'\n')
              frun.write('cd ..\n')
              frun.write('start /B /D '+containername+' cmd /c vvp a.out >'+containername+'\\concoreout.txt\n')
              fdebug.write('cd '+containername+'\n')
              fdebug.write(VWIN+' '+sourcecode+'\n')
              fdebug.write('cd ..\n')
              fdebug.write('start /D '+containername+' cmd /K vvp a.out\n')
              #fdebug.write('start /D '+containername+' cmd /K "'+CPPWIN+' '+sourcecode+'|a"\n')
          elif langext=="m":  #3/23/21
              if M_IS_OCTAVE:   
                  frun.write('start /B /D '+containername+" "+OCTAVEWIN+' -qf --eval "run('+"'"+sourcecode+"'"+')"'+" >"+containername+"\\concoreout.txt\n")
                  fdebug.write('start /D '+containername+" cmd /K " +OCTAVEWIN+' -qf --eval "run('+"'"+sourcecode+"'"+')"'+"\n")
              else:  #  4/2/21
                  frun.write('start /B /D '+containername+" "+MATLABWIN+' -batch "run('+"'"+sourcecode+"'"+')"'+" >"+containername+"\\concoreout.txt\n")
                  fdebug.write('start /D '+containername+" cmd /K " +MATLABWIN+' -batch "run('+"'"+sourcecode+"'"+')"'+"\n")
      else:
          if langext=="py":
              frun.write('(cd '+containername+";"+PYTHONEXE+" "+sourcecode+" >concoreout.txt&echo $!>concorepid)&\n")
              if ubuntu:
                  fdebug.write('concorewd=`pwd`\n')
                  fdebug.write('xterm -e bash -c "cd $concorewd/'+containername+";"+PYTHONEXE+" "+sourcecode+';bash"&\n')
              else:
                  fdebug.write('concorewd=`pwd`\n')
                  fdebug.write('osascript -e "tell application \\"Terminal\\" to do script \\"cd $concorewd/'+containername+";"+PYTHONEXE+" "+sourcecode+'\\""\n')
          elif langext=="cpp": # 6/22/21
              frun.write('(cd '+containername+";"+CPPEXE+" "+sourcecode+";./a.out >concoreout.txt&echo $!>concorepid)&\n")
              if ubuntu:
                  fdebug.write('concorewd=`pwd`\n')
                  fdebug.write('xterm -e bash -c "cd $concorewd/'+containername+";"+CPPEXE+" "+sourcecode+';./a.out;bash"&\n')
              else:
                  fdebug.write('concorewd=`pwd`\n')
                  fdebug.write('osascript -e "tell application \\"Terminal\\" to do script \\"cd $concorewd/'+containername+";"+CPPEXE+" "+sourcecode+';./a.out\\""\n')
          elif langext=="v": # 6/25/21
              frun.write('(cd '+containername+";"+VEXE+" "+sourcecode+";./a.out >concoreout.txt&echo $!>concorepid)&\n")
              if ubuntu:
                  fdebug.write('concorewd=`pwd`\n')
                  fdebug.write('xterm -e bash -c "cd $concorewd/'+containername+";"+VEXE+" "+sourcecode+';./a.out;bash"&\n')
              else:
                  fdebug.write('concorewd=`pwd`\n')
                  fdebug.write('osascript -e "tell application \\"Terminal\\" to do script \\"cd $concorewd/'+containername+";"+VEXE+" "+sourcecode+';vvp a.out\\""\n')
          elif langext=="sh": # 5/19/21
              frun.write('(cd '+containername+";./"+sourcecode+" "+ MCRPATH + " >concoreout.txt&echo $!>concorepid)&\n")
              if ubuntu:
                  fdebug.write('concorewd=`pwd`\n')
                  fdebug.write('xterm -e bash -c "cd $concorewd/'+containername+";./"+sourcecode+' '+MCRPATH+';bash"&\n')
              else: # 11/23/21 MCRPATH
                  fdebug.write('concorewd=`pwd`\n')
                  fdebug.write('osascript -e "tell application \\"Terminal\\" to do script \\"cd $concorewd/'+containername+";./"+sourcecode+' '+MCRPATH+'\\""\n')
          elif langext=="m":  #3/23/21
              if M_IS_OCTAVE:
                  frun.write('(cd '+containername+";"+ OCTAVEEXE+' -qf --eval run\\(\\'+"'"+sourcecode+"\\'"+'\\)'+" >concoreout.txt&echo $!>concorepid)&\n")
                  if ubuntu:
                      fdebug.write('concorewd=`pwd`\n')
                      fdebug.write('xterm -e bash -c "cd $concorewd/'+containername+";"+OCTAVEEXE+' -qf --eval run\\(\\'+"'"+sourcecode+"\\'"+'\\);bash"&'+"\n")
                  else:
                      fdebug.write('concorewd=`pwd`\n')
                      fdebug.write('osascript -e "tell application \\"Terminal\\" to do script \\"cd $concorewd/'+containername+";"+OCTAVEEXE+' -qf --eval run\\\\\\(\\\\\\'+"'"+sourcecode+"\\\\\\'"+'\\\\\\)\\""'+"\n")
              else:  #  4/2/21
                  frun.write('(cd '
+containername+";"+ MATLABEXE+' -batch run\\(\\'+"'"+sourcecode+"\\'"+'\\)'+" >concoreout.txt&echo $!>concorepid)&\n")
                  if ubuntu:
                      fdebug.write('concorewd=`pwd`\n')
                      fdebug.write('xterm -e bash -c "cd $concorewd/' +containername+";"+ MATLABEXE+' -batch run\\(\\'+"'"+sourcecode+"\\'"+'\\);bash"&\n' )
                  else:
                      fdebug.write('concorewd=`pwd`\n')
                      fdebug.write('osascript -e "tell application \\"Terminal\\" to do script \\"cd $concorewd/' +containername+";"+ MATLABEXE+' -batch run\\\\\\(\\\\\\'+"'"+sourcecode+"\\\\\\'"+'\\\\\\)\\""\n' )

if concoretype=="posix":
    fstop.write('#!/bin/bash' + "\n")
i=0 #  3/30/21
for node in nodes_dict:
    containername,sourcecode = nodes_dict[node].split(':')
    if len(sourcecode)!=0:
        dockername = sourcecode.split(".")[0] # 3/28/21
        if concoretype=="windows":
            fstop.write('cmd /C '+containername+"\\concorekill\n")
            fstop.write('del '+containername+"\\concorekill.bat\n")
        else:
            fstop.write('kill -9 `cat '+containername+"/concorepid`\n")
            fstop.write('rm '+containername+"/concorepid\n")
    i=i+1
fstop.close()

if concoretype=="posix":
    fclear.write('#!/bin/bash' + "\n")
i=0 #  9/13/21
for node in nodes_dict:
    containername,sourcecode = nodes_dict[node].split(':')
    if len(sourcecode)!=0:
        dockername = sourcecode.split(".")[0] #3/28/21
        writeedges = volswr[i]
        while writeedges.find(":") != -1: 
            if concoretype=="windows":
                fclear.write('del /Q' + writeedges.split(":")[0].split("-v")[1]+ "\\*\n")
            else:
                fclear.write('rm ' + writeedges.split(":")[0].split("-v")[1]+ "/*\n")
            writeedges = writeedges[writeedges.find(":")+1:]
    i=i+1
fclear.close()

if concoretype=="posix":
    fmaxtime.write('#!/bin/bash' + "\n")
i=0 #  9/12/21
for node in nodes_dict:
    containername,sourcecode = nodes_dict[node].split(':')
    if len(sourcecode)!=0:
        dockername = sourcecode.split(".")[0] #3/28/21
        writeedges = volswr[i]
        while writeedges.find(":") != -1: 
            if concoretype=="windows":
                fmaxtime.write('echo %1 >' + writeedges.split(":")[0].split("-v")[1]+ "\\concore.maxtime\n")
            else:
                fmaxtime.write('echo "$1" >' + writeedges.split(":")[0].split("-v")[1]+ "/concore.maxtime\n")
            writeedges = writeedges[writeedges.find(":")+1:]
    i=i+1
fmaxtime.close()

i=0 #  9/18/22
for node in nodes_dict:
    containername,sourcecode = nodes_dict[node].split(':')
    if len(sourcecode)!=0:
        dockername = sourcecode.split(".")[0] #3/28/21
        writeedges = volswr[i]
        while writeedges.find(":") != -1: 
            if concoretype=="windows":
                fparams.write('echo %1 >' + writeedges.split(":")[0].split("-v")[1]+ "\\concore.params\n")
            else:
                fparams.write('echo "$1" >' + writeedges.split(":")[0].split("-v")[1]+ "/concore.params\n")
            writeedges = writeedges[writeedges.find(":")+1:]
    i=i+1
fparams.close()


i=0 #  9/12/21
for node in nodes_dict:
    containername,sourcecode = nodes_dict[node].split(':')
    if len(sourcecode)!=0:
        dockername = sourcecode.split(".")[0] #3/28/21
        writeedges = volswr[i]
        while writeedges.find(":") != -1: 
            if concoretype=="windows":
                funlock.write('copy %HOMEDRIVE%%HOMEPATH%\concore.apikey' + writeedges.split(":")[0].split("-v")[1]+ "\\concore.apikey\n")
            else:
                funlock.write('cp ~/concore.apikey ' + writeedges.split(":")[0].split("-v")[1]+ "/concore.apikey\n")
            writeedges = writeedges[writeedges.find(":")+1:]
    i=i+1
funlock.close()


frun.close()
fbuild.close()
fdebug.close()
fstop.close()
fclear.close()
fmaxtime.close()
fparams.close()
if concoretype != "windows":
    os.chmod(outdir+"/build",stat.S_IRWXU)
    os.chmod(outdir+"/run",stat.S_IRWXU)
    os.chmod(outdir+"/debug",stat.S_IRWXU)
    os.chmod(outdir+"/stop",stat.S_IRWXU)  
    os.chmod(outdir+"/clear",stat.S_IRWXU) 
    os.chmod(outdir+"/maxtime",stat.S_IRWXU) 
    os.chmod(outdir+"/params",stat.S_IRWXU) 
    os.chmod(outdir+"/unlock",stat.S_IRWXU) 

