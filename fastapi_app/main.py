from fastapi import FastAPI , status
from pydantic import BaseModel
from typing import Optional
import httpx

app = FastAPI()

class AnalyzePRRequest(BaseModel):
    repo_url : str
    pr_number : str
    github_token : Optional[str]  =  None
    
@app.post('/start-task')
async def start_task_endpoint(task_request : AnalyzePRRequest):
    data = {
        "repo_url" : task_request.repo_url,
        "pr_number": task_request.pr_number,
        "github_token" : task_request.github_token
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post("http://127.0.0.1:8000/start-task/", data=data)
        
        if response.status_code != 200:
            return { "task_id": "error", "message": "Failed to start task"}

    print(data)
    task_id = response.json().get('task_id')
    return {"task_id" : task_id , "status" : "task started "}

@app.get('/task-status/{task_id}/')
async def task_status_endpoint(task_id:str):

    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://127.0.0.1:8000/task-status/{task_id}/")
        
        return response.json()

    return {"task_id": task_id, "status": "error", "message": "Failed to retrieve task status"}