from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import httpx
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
import json

app = FastAPI()

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# In-memory user storage (replace with database in production)
USERS_DB: Dict[str, Dict] = {}
REFRESH_TOKENS_DB: Dict[str, str] = {}
ANALYSIS_HISTORY: Dict[str, list] = {}

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

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class AnalyzePRRequest(BaseModel):
    repo_url: str
    pr_number: str
    github_token: Optional[str] = None

# ==================== JWT Utilities ====================
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def get_current_user(request: Request) -> dict:
    """Dependency to verify JWT token from Authorization header"""
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
    
    token = parts[1]
    payload = verify_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return {"email": email}

# ==================== Authentication Routes ====================
@app.post("/api/auth/register", response_model=TokenResponse)
async def register(user: UserRegister):
    """Register a new user"""
    # Check if user already exists
    if user.email in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Store user (in production, use database)
    hashed_password = hash_password(user.password)
    USERS_DB[user.email] = {
        "email": user.email,
        "username": user.username,
        "password_hash": hashed_password,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": user.email})
    REFRESH_TOKENS_DB[refresh_token] = user.email
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(user: UserLogin):
    """Login user and return tokens"""
    # Check if user exists
    if user.email not in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    db_user = USERS_DB[user.email]
    if not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": user.email})
    REFRESH_TOKENS_DB[refresh_token] = user.email
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@app.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    payload = verify_token(req.refresh_token)
    email = payload.get("sub")
    
    if req.refresh_token not in REFRESH_TOKENS_DB:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new access token
    access_token = create_access_token(
        data={"sub": email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(access_token=access_token, refresh_token=req.refresh_token)

@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (token will be invalid after expiration)"""
    return {"message": "Logged out successfully"}

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    email = current_user["email"]
    if email not in USERS_DB:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    user = USERS_DB[email]
    return {
        "email": user["email"],
        "username": user["username"],
        "created_at": user["created_at"]
    }

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
    current_user: dict = Depends(get_current_user)
):
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
                "http://127.0.0.1:8001/start-task/", json=data
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

        # Store in history
        email = current_user["email"]
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

@app.get("/api/analyze/status/{task_id}")
async def task_status_endpoint(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Checks the status of a running task by forwarding to the internal service.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"http://127.0.0.1:8001/task-status/{task_id}/")

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

@app.get("/api/analyze/history")
async def get_analysis_history(current_user: dict = Depends(get_current_user)):
    """Get user's analysis history with current task status"""
    email = current_user["email"]
    history = ANALYSIS_HISTORY.get(email, [])
    
    # Update status for each task by checking with Django backend
    updated_history = []
    for item in history:
        task_id = item.get("task_id")
        if task_id:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"http://127.0.0.1:8001/task-status/{task_id}/")
                    if response.status_code == 200:
                        task_data = response.json()
                        item["status"] = task_data.get("status", "unknown")
            except:
                # If backend is unreachable, keep existing status
                pass
        updated_history.append(item)
    
    return {"history": updated_history}

# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

