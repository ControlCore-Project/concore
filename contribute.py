import github
from github import Github, UnknownObjectException
import sys,os

# BOT_TOKEN = sys.argv[1]
# REPO_NAME = sys.argv[2]
# OWNER_NAME = sys.argv[3]
# PR_TITLE = sys.argv[4]
# PR_BODY = sys.argv[5]
# AUTHOR_NAME = sys.argv[6]
# STUDY_NAME = sys.argv[7]
# STUDY_NAME_PATH = sys.argv[8]
g = Github("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")
repo = g.get_user("parteekcoder123").get_repo("concore")
mainRepo = g.get_repo("parteekcoder/concore")
# for i in mainRepo.get_issues():
#     print(i)
# base_ref = repo.get_branch(repo.default_branch).commit.sha
# branches = repo.get_branches()
# is_present = False
# branch_name = AUTHOR_NAME+STUDY_NAME
# for branch in branches:
#     if branch.name == branch_name:
#         is_present = True
#         break
    
# if not is_present:
#     new_ref = repo.create_git_ref(f'refs/heads/{branch_name}', base_ref)
# dir_path = AUTHOR_NAME + '_' + STUDY_NAME
# try:
#     contents = repo.get_contents(dir_path, ref=repo.default_branch)
#     for filename in os.listdir(STUDY_NAME_PATH):
#         with open(os.path.join(STUDY_NAME_PATH, filename), 'r') as file:
#             new_file_contents = file.read()
#         file_path = f'{dir_path}/{filename}'
#         try:
#             file_contents = repo.get_contents(file_path, ref=branch_name)
#             if file_contents.decoded_content.decode("utf-8") != new_file_contents:
#                 file_sha = repo.get_contents(file_path, ref=repo.default_branch).sha
#                 message = f'Update file {filename}'
#                 repo.update_file(file_path, message, new_file_contents, file_sha, branch=branch_name)
#         except:
#             message = f'Add file {filename}'
#             repo.create_file(file_path, message, new_file_contents, branch=branch_name)
# except github.GithubException as e:
#     if e.status == 404:
#         for filename in os.listdir(STUDY_NAME_PATH):
#             with open(os.path.join(STUDY_NAME_PATH, filename), 'r') as file:
#                 content = file.read()
#             file_path = f'{dir_path}/{filename}'
#             message = f'Add file {filename}'
#             repo.create_file(file_path, message, content, branch=branch_name)
#     else:
#         raise e
# head_ref = f'{OWNER_NAME}:{branch_name}'
# base_ref = mainRepo.default_branch

print(mainRepo)
pr = repo.create_pull(title="PR_TITLE", body="PR_BODY", base="parteekcoder123/concore:main",head="main")
resp = f'Pull request created: {pr.html_url}'
print(resp)
