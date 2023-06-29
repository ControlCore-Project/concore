import github
from github import Github
import os,sys,time,platform,base64

# Intializing the Variables
# Hashed token
BOT_TOKEN = 'Z2l0aHViX3BhdF8xMUFYS0pGVFkwd2xwT0dmYldFOTBBXzN3Nkx2THpiaUFKek5pTDdqNlpLUzVwUUpoTlJWR3dtNnM0NWNDa0RmWTJaTTZLSUpHRHhERlhrZlJS'
REPO_NAME = 'concore-studies'        #repo name
OWNER_NAME = 'parteekcoder123'  #bot account name
STUDY_NAME =  sys.argv[1]
STUDY_NAME_PATH =  sys.argv[2]
AUTHOR_NAME =  sys.argv[3]
BRANCH_NAME =  sys.argv[4]
PR_TITLE =  sys.argv[5]
PR_BODY =  sys.argv[6]
UPSTREAM_OWNER = 'ControlCore-Project'   # upstream to which examples should be contributed

# Defining Functions
def checkInputValidity():
    if AUTHOR_NAME=="" or STUDY_NAME=="" or STUDY_NAME=="":
        print("Please Provide necessary Inputs")
        exit(0)
    if not os.path.isdir(STUDY_NAME_PATH):
        print("Directory doesnot Exists.Invalid Path")
        exit(0)


def getPRs(upstream_repo):
    try:
        return upstream_repo.get_pulls(head=f'{OWNER_NAME}:{BRANCH_NAME}')
    except Exception as e:
        print("Not able to fetch Status of your example.Please try after some time.")
        exit(0)

def printPR(pr):
    print(f'Check your example here https://github.com/{UPSTREAM_OWNER}/pulls/'+str(pr.number),end="")

def anyOpenPR(upstream_repo):
    pr = getPRs(upstream_repo)
    openPr=None
    for i in pr:
        if i.state=="open":
            openPr=i
            break
    return openPr

def commitAndUpdateRef(upstream_repo,repo,tree_content,commit,branch):
    try:
        new_tree = repo.create_git_tree(tree=tree_content,base_tree=commit.commit.tree)
        new_commit = repo.create_git_commit("commit message",new_tree,[commit.commit])
        if len(repo.compare(base=commit.commit.sha,head=new_commit.sha).files) == 0:
            print("Your don't have any new changes.May be your example is already accepted.If this is not the case try with different fields.")
            exit(0)
        ref = repo.get_git_ref("heads/"+branch.name)
        ref.edit(new_commit.sha,True)
    except Exception as e:
        print("failed to Upload your example.Please try after some time.",end="")
        exit(0)


def appendBlobInTree(repo,content,file_path,tree_content):
    blob = repo.create_git_blob(content,'utf-8')
    tree_content.append( github.InputGitTreeElement(path=file_path,mode="100644",type="blob",sha=blob.sha))


def fetchUpstream(repo,base_sha,branch):
    try:
        result = repo.compare(base=base_sha,head=branch.commit.commit.sha)
        if result.behind_by>0:
            ref = repo.get_git_ref("heads/"+branch.name)
            ref.edit(base_sha)
    except Exception as e:
        exit(0)


def runWorkflow(repo,upstream_repo):
    openPR = anyOpenPR(upstream_repo)
    if openPR==None:
        workflow_runned = repo.get_workflow(id_or_name="pull_request.yml").create_dispatch(ref=BRANCH_NAME,inputs={'title':PR_TITLE,'body':PR_BODY,'upstreamRepo':UPSTREAM_OWNER,'botRepo':OWNER_NAME,'repo':REPO_NAME})
        if not workflow_runned:
            print("Some error occured.Please try after some time")
            exit(0)
        else:
            printPRStatus(upstream_repo)
    else:
        print("Successfully uploaded all files,your example is in waiting.Please wait for us to accept it.",end="")
        printPR(openPR)

def printPRStatus(upstream_repo):
    try:
        time.sleep(15)
        openPR = anyOpenPR(upstream_repo)
        if openPR==None:
            print("Someting went wrong or your example already exist.If this is not the case try with different fields")
            exit(0)
        printPR(openPR)
    except Exception as e:
        print("Your example successfully uploaded but unable to fetch status.Please try again")
    

def isImageFile(filename):
    image_extensions = ['.jpeg', '.jpg', '.png']
    _, file_extension = os.path.splitext(filename)
    return file_extension.lower() in image_extensions

# Encode Github Token
# def encode_token(token):
#     encoded_bytes = base64.b64encode(token.encode('utf-8'))
#     encoded_token = encoded_bytes.decode('utf-8')
#     return encoded_token


# Decode Github Token
def decode_token(encoded_token):
    decoded_bytes = base64.b64decode(encoded_token.encode('utf-8'))
    decoded_token = decoded_bytes.decode('utf-8')
    return decoded_token


# check if directory path is Valid
checkInputValidity()


# Authenticating Github with Access token
try:
    if BRANCH_NAME=="#":
        BRANCH_NAME=AUTHOR_NAME+"_"+STUDY_NAME
    if PR_TITLE=="#":
        PR_TITLE="Contributing Study "+AUTHOR_NAME+" "+STUDY_NAME
    if PR_BODY=="#":
        PR_BODY="Study Contributed by "+ AUTHOR_NAME
    AUTHOR_NAME = AUTHOR_NAME.replace(" ","_")
    DIR_PATH = AUTHOR_NAME + '_' + STUDY_NAME
    g = Github(decode_token(BOT_TOKEN))
    repo = g.get_user(OWNER_NAME).get_repo(REPO_NAME)
    upstream_repo = g.get_repo(f'{UPSTREAM_OWNER}/{REPO_NAME}') #controlcore-Project/concore
    base_ref = upstream_repo.get_branch(repo.default_branch)
    branches = repo.get_branches()
    BRANCH_NAME = BRANCH_NAME.replace(" ","_")
    DIR_PATH = DIR_PATH.replace(" ","_")
    is_present = any(branch.name == BRANCH_NAME for branch in branches)
except:
    print("Some error occured.Authentication failed",end="")
    exit(0)


try:
    # If creating PR First Time
    # Create New Branch for that exmaple
    if not is_present:
        repo.create_git_ref(f'refs/heads/{BRANCH_NAME}', base_ref.commit.sha)
    # Get current branch
    branch = repo.get_branch(branch=BRANCH_NAME)
except Exception as e:
    print("Not able to create study for you.Please try again after some time",end="")
    exit(0)


tree_content = []

try:
    for root, dirs, files in os.walk(STUDY_NAME_PATH):
        for filename in files:
            path = os.path.join(root, filename)
            if isImageFile(filename):
                with open(path, 'rb') as file:
                    image = file.read()
                    content = base64.b64encode(image).decode('utf-8')
            else:
                with open(path, 'r') as file:
                    content = file.read()
            file_path = f'{DIR_PATH+path.removeprefix(STUDY_NAME_PATH)}'
            if(platform.uname()[0]=='Windows'): file_path=file_path.replace("\\","/")
            appendBlobInTree(repo,content,file_path,tree_content)
    commitAndUpdateRef(upstream_repo,repo,tree_content,base_ref.commit,branch)
    runWorkflow(repo,upstream_repo)
except Exception as e:
    print("Some error Occured.Please try again after some time.",end="")
    exit(0)