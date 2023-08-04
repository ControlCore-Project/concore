import github
from github import Github
import os,sys,platform,base64,time

# Intializing the Variables
# Hashed token
BOT_TOKEN = "Z2l0aHViX3BhdF8xMUFYS0pGVFkwODR5OEhoZlI5VEl1X0VZZnNaNjU0WGw4OU0ycXhJc0h3TXh3RkVIZGFRQ3gwa0daZFhKUUdYbUk2QzRTU1dDNkF4clUyQWRF"
BOT_ACCOUNT = 'concore-bot'        #bot account name
REPO_NAME = 'concore-studies'        #study repo name
UPSTREAM_ACCOUNT = 'ControlCore-Project'  #upstream account name
STUDY_NAME =  sys.argv[1]
STUDY_NAME_PATH =  sys.argv[2]
AUTHOR_NAME =  sys.argv[3]
BRANCH_NAME =  sys.argv[4]
PR_TITLE =  sys.argv[5]
PR_BODY =  sys.argv[6]

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
        return upstream_repo.get_pulls(head=f'{BOT_ACCOUNT}:{BRANCH_NAME}')
    except Exception as e:
        print("Not able to fetch Status of your example.Please try after some time.")
        exit(0)

def printPR(pr):
    print(f'Check your example here https://github.com/{UPSTREAM_ACCOUNT}/{REPO_NAME}/pulls/{pr.number}',end="")

def anyOpenPR(upstream_repo):
    pr = getPRs(upstream_repo)
    openPr=None
    for i in pr:
        if i.state=="open":
            openPr=i
            break
    return openPr

def commitAndUpdateRef(repo,tree_content,commit,branch):
    try:
        new_tree = repo.create_git_tree(tree=tree_content,base_tree=commit.commit.tree)
        new_commit = repo.create_git_commit("commit study",new_tree,[commit.commit])
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


def runWorkflow(repo,upstream_repo):
    openPR = anyOpenPR(upstream_repo)
    if openPR==None:
        workflow_runned = repo.get_workflow(id_or_name="pull_request.yml").create_dispatch(ref=BRANCH_NAME,inputs={'title':f"[BOT]: {PR_TITLE}",'body':PR_BODY,'upstreamRepo':UPSTREAM_ACCOUNT,'botRepo':BOT_ACCOUNT,'repo':REPO_NAME})
        if not workflow_runned:
            print("Some error occured. Please try after some time")
            exit(0)
        else:
            printPRStatus(upstream_repo)
    else:
        print("Successfully uploaded all files, your example is in waiting.Please wait for us to accept it.",end="")
        printPR(openPR)

def printPRStatus(upstream_repo):
    try:
        issues = upstream_repo.get_issues()
        pulls = upstream_repo.get_pulls(state='all')
        max_num = -1
        for i in issues:
            max_num = max(max_num,i.number)
        for i in pulls:
            max_num = max(max_num,i.number)
        time.sleep(4)
        print(f'Check your example here https://github.com/{UPSTREAM_ACCOUNT}/{REPO_NAME}/pulls/{max_num+1}',end="")
    except Exception as e:
        print("Your example successfully uploaded but unable to fetch status. Please try again")
    

def isImageFile(filename):
    image_extensions = ['.jpeg', '.jpg', '.png','.gif']
    return any(filename.endswith(ext) for ext in image_extensions)

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


# Decode Github Token
def decode_token(encoded_token):
    decoded_bytes = encoded_token.encode("ascii")
    convertedbytes = base64.b64decode(decoded_bytes)
    decoded_token = convertedbytes.decode("ascii")
    print('token decoded successfully')
    return decoded_token


# check if directory path is Valid
checkInputValidity()


# Authenticating Github with Access token
try:
    if BRANCH_NAME=="#":
        BRANCH_NAME=AUTHOR_NAME+"_"+STUDY_NAME
    if PR_TITLE=="#":
        PR_TITLE=f"Contributing Study {STUDY_NAME} by {AUTHOR_NAME}"
    if PR_BODY=="#":
        PR_BODY=f"Study Name: {STUDY_NAME} \n Author Name: {AUTHOR_NAME}"
    AUTHOR_NAME = AUTHOR_NAME.replace(" ","_")
    DIR_PATH = STUDY_NAME
    g = Github(decode_token(BOT_TOKEN))
    repo = g.get_user(BOT_ACCOUNT).get_repo(REPO_NAME)
    upstream_repo = g.get_repo(f'{UPSTREAM_ACCOUNT}/{REPO_NAME}') #controlcore-Project/concore-studies
    base_ref = upstream_repo.get_branch(repo.default_branch)
    branches = repo.get_branches()
    BRANCH_NAME = BRANCH_NAME.replace(" ","_")
    DIR_PATH = DIR_PATH.replace(" ","_")
    is_present = any(branch.name == BRANCH_NAME for branch in branches)
except Exception as e:
    print("Authentication failed", end="")
    exit(0)


try:
    # If creating PR First Time
    # Create New Branch for that exmaple
    if not is_present:
        repo.create_git_ref(f'refs/heads/{BRANCH_NAME}', base_ref.commit.sha)
    # Get current branch
    branch = repo.get_branch(branch=BRANCH_NAME)
except Exception as e:
    print("Not able to create study for you. Please try again after some time", end="")
    exit(0)


tree_content = []

try:
    for root, dirs, files in os.walk(STUDY_NAME_PATH):
        for filename in files:
            path = f"{root}/{filename}"
            if isImageFile(filename):
                with open(path, 'rb') as file:
                    image = file.read()
                    print('image processing')
                    content = base64.b64encode(image).decode('utf-8')
            else:
                with open(path, 'r') as file:
                    content = file.read()
            file_path = f'{DIR_PATH+remove_prefix(path,STUDY_NAME_PATH)}'
            if(platform.uname()[0]=='Windows'): file_path=file_path.replace("\\","/")
            appendBlobInTree(repo,content,file_path,tree_content)
    commitAndUpdateRef(repo,tree_content,base_ref.commit,branch)
    runWorkflow(repo,upstream_repo)
except Exception as e:
    print(e)
    print("Some error Occured.Please try again after some time.",end="")
    exit(0)