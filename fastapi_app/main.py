from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx
import os
from datetime import datetime

app = FastAPI()

# Django Backend Configuration
DJANGO_BACKEND_URL = os.getenv("DJANGO_BACKEND_URL", "http://127.0.0.1:8001")
ANALYSIS_HISTORY: dict = {}

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ==================== Models ====================
class UserRegister(BaseModel):
    email: str
    password: str
    username: str

class UserLogin(BaseModel):
    email: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class AnalyzePRRequest(BaseModel):
    repo_url: str
    pr_number: str
    github_token: Optional[str] = None

# ==================== Helper Functions ====================
def get_token_from_request(request: Request) -> str:
    """Extract JWT token from Authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    return parts[1]

# ==================== Authentication Routes (Proxy to Django) ====================
@app.post("/api/auth/register")
async def register(user: UserRegister):
    """Register a new user - proxies to Django"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{DJANGO_BACKEND_URL}/auth/register/",
                json=user.dict()
            )
        
        if response.is_error:
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Backend timeout"
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Backend error: {str(exc)}"
        )

@app.post("/api/auth/login")
async def login(user: UserLogin):
    """Login user - proxies to Django"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{DJANGO_BACKEND_URL}/auth/login/",
                json=user.dict()
            )
        
        if response.is_error:
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Backend timeout"
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Backend error: {str(exc)}"
        )

@app.post("/api/auth/refresh")
async def refresh_token(req: RefreshTokenRequest):
    """Refresh access token - proxies to Django"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{DJANGO_BACKEND_URL}/auth/refresh/",
                json=req.dict()
            )
        
        if response.is_error:
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Backend timeout"
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Backend error: {str(exc)}"
        )

@app.post("/api/auth/logout")
async def logout(request: Request):
    """Logout user - proxies to Django"""
    try:
        token = get_token_from_request(request)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{DJANGO_BACKEND_URL}/auth/logout/",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        if response.is_error:
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Backend timeout"
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Backend error: {str(exc)}"
        )

@app.get("/api/auth/me")
async def get_me(request: Request):
    """Get current user info - proxies to Django"""
    try:
        token = get_token_from_request(request)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{DJANGO_BACKEND_URL}/auth/me/",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        if response.is_error:
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
        
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
    
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Backend timeout"
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Backend error: {str(exc)}"
        )


# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ==================== Frontend Routes ====================
@app.get("/")
async def read_root():
    """Serve the landing page"""
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/login")
async def login_page():
    """Serve login page"""
    return FileResponse(os.path.join(static_dir, "login.html"))

@app.get("/register")
async def register_page():
    """Serve register page"""
    return FileResponse(os.path.join(static_dir, "register.html"))

@app.get("/dashboard")
async def dashboard_page():
    """Serve dashboard page"""
    return FileResponse(os.path.join(static_dir, "dashboard.html"))

@app.get("/history")
async def history_page():
    """Serve history page"""
    return FileResponse(os.path.join(static_dir, "history.html"))

# ==================== PR Analysis Routes ====================
@app.post("/api/analyze/start", status_code=status.HTTP_202_ACCEPTED)
async def start_task_endpoint(
    task_request: AnalyzePRRequest,
    request: Request
):
    """
    Start a PR analysis task - validates with Django then forwards to celery
    """
    try:
        token = get_token_from_request(request)
        
        # Verify token with Django
        async with httpx.AsyncClient(timeout=10.0) as client:
            verify_response = await client.get(
                f"{DJANGO_BACKEND_URL}/auth/me/",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        if verify_response.is_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_data = verify_response.json()
        email = user_data.get('email')
        
        data = {
            "repo_url": task_request.repo_url,
            "pr_number": task_request.pr_number,
            "github_token": task_request.github_token or "",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{DJANGO_BACKEND_URL}/start-task/", 
                json=data,
                headers={"Authorization": f"Bearer {token}"}
            )

        if response.is_error:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to start task: {response.text}",
            )

        result = response.json()
        task_id = result.get("task_id")

        if not task_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No task_id returned from backend",
            )

        # Store in history
        if email not in ANALYSIS_HISTORY:
            ANALYSIS_HISTORY[email] = []
        
        ANALYSIS_HISTORY[email].append({
            "task_id": task_id,
            "repo_url": task_request.repo_url,
            "pr_number": task_request.pr_number,
            "created_at": datetime.utcnow().isoformat(),
            "status": "processing"
        })

        return {"task_id": task_id, "status": "Task started"}

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Backend timeout",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Backend error: {str(exc)}",
        )

@app.get("/api/analyze/status/{task_id}")
async def task_status_endpoint(
    task_id: str,
    request: Request
):
    """
    Get task status - validates auth then checks status
    """
    try:
        token = get_token_from_request(request)
        
        # Verify token with Django
        async with httpx.AsyncClient(timeout=10.0) as client:
            verify_response = await client.get(
                f"{DJANGO_BACKEND_URL}/auth/me/",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        if verify_response.is_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{DJANGO_BACKEND_URL}/task-status/{task_id}/",
                headers={"Authorization": f"Bearer {token}"}
            )

        if response.is_error:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch task status",
            )

        return response.json()

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Backend timeout",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Backend error: {str(exc)}",
        )

@app.get("/api/analyze/history")
async def get_analysis_history(request: Request):
    """Get user's analysis history with current task status"""
    try:
        token = get_token_from_request(request)
        
        # Verify token with Django
        async with httpx.AsyncClient(timeout=10.0) as client:
            verify_response = await client.get(
                f"{DJANGO_BACKEND_URL}/auth/me/",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        if verify_response.is_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_data = verify_response.json()
        email = user_data.get('email')
        
        history = ANALYSIS_HISTORY.get(email, [])
        
        # Update status for each task
        updated_history = []
        for item in history:
            task_id = item.get("task_id")
            if task_id:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(
                            f"{DJANGO_BACKEND_URL}/task-status/{task_id}/",
                            headers={"Authorization": f"Bearer {token}"}
                        )
                        if response.status_code == 200:
                            task_data = response.json()
                            item["status"] = task_data.get("status", "unknown")
                except:
                    pass
            updated_history.append(item)
        
        return {"history": updated_history}
    
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Backend timeout",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Backend error: {str(exc)}",
        )

# ==================== Health Check ====================
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

