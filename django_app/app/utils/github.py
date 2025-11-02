import requests 
import base64
from urllib.parse import urlparse
import uuid
from .ai_agent import analyze_code

def get_owner_and_repo(url):
    passed_url = urlparse(url) # it gives various details about this url and like about path of this url
    path_parts = passed_url.path.strip('/').split('/')
    if len(path_parts) >= 2:
        owner , repo = path_parts[0] , path_parts[1]
        return owner , repo
    return None , None 

def fetch_pr_files(repo_url , pr_number , github_token = None):
    owner , repo = get_owner_and_repo(repo_url)
    if not owner or not repo:
        raise ValueError("Invalid GitHub repository URL")

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    headers = {}
    if github_token:
        headers['Authorization'] = f'token {github_token}'

    response = requests.get(api_url, headers=headers )
    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR files: {response.status_code} - {response.text}")

    return response.json()\
        
def fetch_files_content(repo_url , file_path , github_token = None):
    owner , repo = get_owner_and_repo(repo_url)
    if not owner or not repo:
        raise ValueError("Invalid GitHub repository URL")

    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    headers = {}
    if github_token:
        headers['Authorization'] = f'token {github_token}'

    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR files: {response.status_code} - {response.text}")

    content_data = response.json()
    return base64.b64decode(content_data['content']).decode('utf-8')   # change the content_data from base64 into readable form so use b64decode function for that


def analysis_pr(repo_url , pr_number , github_token  = None):
    task_id = str(uuid.uuid4())
    try :
        pr_files = fetch_pr_files(repo_url , pr_number , github_token)
        analysis_results = []
        for files in pr_files:
            file_name = files['filename']
            raw_content = fetch_files_content(repo_url , file_name , github_token)
            print("DEBUG: filename:", file_name)
            print("DEBUG: file content length:", len(raw_content))
            print("DEBUG: file content preview:", raw_content[:300])

            analysis_res = analyze_code(raw_content , file_name)
            analysis_results.append({
                "filename" : file_name,
                "analysis_result" : analysis_res
            })
        return {"task_id " : task_id , "analysis_result" : analysis_results}
    except Exception as e:
        return {"task_id " : task_id , "error" : str(e)}