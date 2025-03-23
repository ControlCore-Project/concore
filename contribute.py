import github
from github import Github
import os,sys,platform,base64,time

# Intializing the Variables
# Hashed token
BOT_TOKEN = "Z2l0aHViX3BhdF8xMUFYS0pGVFkwU2VhNW9ORjRyN0E5X053WDAwTVBUUU5RVUNTa2lNNlFYZHJET1lZa3B4cTIxS091YVhkeVhUYmRQMzdVUkZaRWpFMjlRRXM5"
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
    if not AUTHOR_NAME or not STUDY_NAME or not STUDY_NAME_PATH:
        print("Please Provide necessary Inputs")
        exit(1)
    if not os.path.isdir(STUDY_NAME_PATH):
        print("Directory doesnot Exists.Invalid Path")
        exit(1)

def printPR(pr):
    print(f'Check your example here https://github.com/{UPSTREAM_ACCOUNT}/{REPO_NAME}/pulls/{pr.number}',end="")

def anyOpenPR(upstream_repo):
    try:
        prs = upstream_repo.get_pulls(state='open', head=f'{BOT_ACCOUNT}:{BRANCH_NAME}')
        return prs[0] if prs.totalCount > 0 else None
    except Exception:
        print("Unable to fetch PR status. Try again later.")
        exit(1)

def commitAndUpdateRef(repo,tree_content,commit,branch):
    try:
        new_tree = repo.create_git_tree(tree=tree_content,base_tree=commit.commit.tree)
        new_commit = repo.create_git_commit(f"Committing Study Named {STUDY_NAME}",new_tree,[commit.commit])
        if len(repo.compare(base=commit.commit.sha,head=new_commit.sha).files) == 0:
            print("Your don't have any new changes.May be your example is already accepted.If this is not the case try with different fields.")
            exit(1)
        ref = repo.get_git_ref("heads/"+branch.name)
        ref.edit(new_commit.sha,True)
    except Exception as e:
        print("failed to Upload your example.Please try after some time.",end="")
        exit(1)


def appendBlobInTree(repo,content,file_path,tree_content):
    blob = repo.create_git_blob(content,'utf-8')
    tree_content.append( github.InputGitTreeElement(path=file_path,mode="100644",type="blob",sha=blob.sha))


def runWorkflow(repo,upstream_repo):
    openPR = anyOpenPR(upstream_repo)
    if not openPR:
        try:
            repo.get_workflow("pull_request.yml").create_dispatch(
                ref=BRANCH_NAME,
                inputs={'title': f"[BOT]: {PR_TITLE}", 'body': PR_BODY, 'upstreamRepo': UPSTREAM_ACCOUNT, 'botRepo': BOT_ACCOUNT, 'repo': REPO_NAME}
            )
            printPRStatus(upstream_repo)
        except Exception as e:
            print(f"Error triggering workflow. Try again later.\n ERROR: {e}")
            exit(1)
    else:
        print(f"Successfully uploaded. Waiting for approval: https://github.com/{UPSTREAM_ACCOUNT}/{REPO_NAME}/pull/{openPR.number}")

def printPRStatus(upstream_repo):
    attempts = 5
    delay = 2
    for i in range(attempts):
        print(f"Attempt: {i}")
        try:
            latest_pr = upstream_repo.get_pulls(state='open', sort='created', direction='desc')[0]
            print(f"Check your example here: https://github.com/{UPSTREAM_ACCOUNT}/{REPO_NAME}/pull/{latest_pr.number}")
            return
        except Exception:
            time.sleep(delay)
            delay *= 2
    print("Uploaded successfully, but unable to fetch status.")


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
    return decoded_token


# check if directory path is Valid
checkInputValidity()


# Authenticating Github with Access token
try:
    BRANCH_NAME = AUTHOR_NAME.replace(" ", "_") + "_" + STUDY_NAME if BRANCH_NAME == "#" else BRANCH_NAME.replace(" ", "_")
    PR_TITLE = f"Contributing Study {STUDY_NAME} by {AUTHOR_NAME}" if PR_TITLE == "#" else PR_TITLE
    PR_BODY = f"Study Name: {STUDY_NAME}\nAuthor Name: {AUTHOR_NAME}" if PR_BODY == "#" else PR_BODY
    DIR_PATH = STUDY_NAME
    DIR_PATH = DIR_PATH.replace(" ","_")
    g = Github(decode_token(BOT_TOKEN))
    repo = g.get_user(BOT_ACCOUNT).get_repo(REPO_NAME)
    upstream_repo = g.get_repo(f'{UPSTREAM_ACCOUNT}/{REPO_NAME}') #controlcore-Project/concore-studies
    base_ref = upstream_repo.get_branch(repo.default_branch)

    try:
        repo.get_branch(BRANCH_NAME)
        is_present = True
    except github.GithubException:
        print(f"No Branch is available with the name {BRANCH_NAME}")
        is_present = False
except Exception as e:
    print("Authentication failed", end="")
    exit(1)


try:
    if not is_present:
        repo.create_git_ref(f"refs/heads/{BRANCH_NAME}", base_ref.commit.sha)
    branch = repo.get_branch(BRANCH_NAME)
except Exception:
    print("Unable to create study. Try again later.")
    exit(1)


tree_content = []

try:
    for root, dirs, files in os.walk(STUDY_NAME_PATH):
        files = [f for f in files if not f[0] == '.']
        for filename in files:
            path = f"{root}/{filename}"
            if isImageFile(filename):
                with open(file=path, mode='rb') as file:
                    image = file.read()
                    content = base64.b64encode(image).decode('utf-8')
            else:
                with open(file=path, mode='r') as file:
                    content = file.read()
            file_path = f'{DIR_PATH+remove_prefix(path,STUDY_NAME_PATH)}'
            if(platform.uname()[0]=='Windows'): file_path=file_path.replace("\\","/")
            appendBlobInTree(repo,content,file_path,tree_content)
    commitAndUpdateRef(repo,tree_content,base_ref.commit,branch)
    runWorkflow(repo,upstream_repo)
except Exception as e:
    print(e)
    print("Some error Occured.Please try again after some time.",end="")
    exit(1)