from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import httpx

app = FastAPI()

class AnalyzePRRequest(BaseModel):
    repo_url: str
    pr_number: str
    github_token: Optional[str] = None


@app.post("/start-task", status_code=status.HTTP_202_ACCEPTED)
async def start_task_endpoint(task_request: AnalyzePRRequest):
    """
    Forwards a task request to the internal service and returns a task ID.
    """
    data = {
        "repo_url": task_request.repo_url,
        "pr_number": task_request.pr_number,
        "github_token": task_request.github_token,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "http://127.0.0.1:8000/start-task/", json=data
            )

        if response.is_error:
            raise HTTPException(
                status_code=response.status_code,
                detail={
                    "error": "Failed to start task",
                    "reason": response.text,
                    "upstream_status": response.status_code,
                },
            )

        result = response.json()
        task_id = result.get("task_id")

        if not task_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No task_id returned from internal service.",
            )

        return {"task_id": task_id, "status": "Task started"}

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Internal service timeout while starting the task.",
        )

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error while connecting to internal service: {exc.request.url}.",
        )


@app.get("/task-status/{task_id}/")
async def task_status_endpoint(task_id: str):
    """
    Checks the status of a running task by forwarding to the internal service.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"http://127.0.0.1:8000/task-status/{task_id}/")

        if response.is_error:
            raise HTTPException(
                status_code=response.status_code,
                detail={
                    "error": "Failed to fetch task status",
                    "reason": response.text,
                    "upstream_status": response.status_code,
                },
            )

        return response.json()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Internal service timeout while fetching task status.",
        )

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error while connecting to internal service: {exc.request.url}.",
        )
