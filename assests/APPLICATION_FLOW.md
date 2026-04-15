# PRPilot - Application Flow (Code + Functionality)

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Browser)                         │
│              HTML, CSS, JS (Static Files)                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│         FASTAPI (Port 8000 - Gateway Layer)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ • Receives HTTP requests from frontend                  │  │
│  │ • Validates JWT tokens                                 │  │
│  │ • Proxies requests to Django backend                   │  │
│  │ • Returns responses to frontend                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│        DJANGO (Port 8001 - Core Backend)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ • Authentication (register/login)                       │  │
│  │ • JWT token generation & validation                     │  │
│  │ • User database management                              │  │
│  │ • Task orchestration                                    │  │
│  │ • Celery task creation & monitoring                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│      CELERY (Background Task Processing)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ • Fetch PR files from GitHub                            │  │
│  │ • Send code to Groq AI for analysis                     │  │
│  │ • Cache results in Redis                                │  │
│  │ • Return results to frontend                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Code Flow (How Data Moves)

### **1. Registration Flow**

```
BROWSER (Login Page)
  ↓ User fills form: email, username, password
  ↓ Click "Register"
  ↓ POST http://localhost:8000/api/auth/register
  │ {email, username, password}
  │
FASTAPI (main.py - /api/auth/register)
  ├─ Extract request data
  ├─ Call Django endpoint
  └─ POST http://127.0.0.1:8001/auth/register/
     │ {email, username, password}
     │
DJANGO (auth_views.py - register function)
  ├─ Validate email format
  ├─ Check if user exists
  ├─ Hash password with bcrypt
  ├─ Save to SQLite database (User model)
  ├─ Generate JWT access_token (30 min)
  ├─ Generate JWT refresh_token (7 days)
  ├─ Save refresh_token to database
  └─ Return JSON response
     │ {access_token, refresh_token, user_info}
     │
FASTAPI (main.py)
  └─ Pass response to browser
     │
BROWSER
  ├─ Save tokens to localStorage
  ├─ Redirect to dashboard
  └─ User logged in 
```

---

### **2. Login Flow**

```
BROWSER (Login Page)
  ↓ User fills: email, password
  ↓ DELETE http://localhost:8000/api/auth/login
  │
FASTAPI (/api/auth/login)
  ├─ Extract credentials
  └─ POST http://127.0.0.1:8001/auth/login/
     │
DJANGO (auth_views.py - login function)
  ├─ Find user by email
  ├─ Verify password with bcrypt
  ├─ Generate new JWT tokens
  └─ Return response
     │
BROWSER
  ├─ Save tokens to localStorage
  ├─ Set Authorization header
  └─ Can now call protected endpoints 
```

---

### **3. PR Analysis Flow (Main Feature)**

```
BROWSER (Dashboard)
  ↓ User enters:
  │ - Repo URL (e.g., https://github.com/rails/rails)
  │ - PR number (e.g., 49283)
  │ - (Optional) GitHub token
  ↓ Click "Analyze PR"
  ↓ POST http://localhost:8000/api/analyze/start
    Header: Authorization: Bearer <access_token>
    Body: {repo_url, pr_number, github_token}
  │
FASTAPI (main.py - start_task_endpoint)
  ├─ Extract token from Authorization header
  ├─ GET http://127.0.0.1:8001/auth/me/
  │  Header: Authorization: Bearer <token>
  │  → Verify token is valid
  ├─ Extract user email from token
  ├─ POST http://127.0.0.1:8001/start-task/
     Header: Authorization: Bearer <token>
     Body: {repo_url, pr_number, github_token}
  │
DJANGO (views.py - start_task function)
  ├─ Validate token using jwt.decode()
  ├─ Extract user_id from token
  ├─ Create Celery task:
  │  └─ analyze_pr_request.delay(repo_url, pr_number, github_token)
  ├─ Get task_id from Celery
  └─ Return response: {task_id, status: "started"}
     │
FASTAPI
  └─ Return task_id to BROWSER
     │
BROWSER
  ├─ Store task_id
  ├─ Display "Analysis in progress..."
  └─ Start polling for status every 2-5 seconds
     │
     ↓ BACKGROUND: CELERY PROCESSING
     │
CELERY WORKER (task.py - analyze_pr_request)
  ├─ Fetch PR files from GitHub API
  │  └─ GET https://api.github.com/repos/{owner}/{repo}/pulls/{pr}/files
  ├─ Loop through each file:
  │  ├─ Read file content
  │  ├─ Send to Groq AI API:
  │  │  └─ POST https://api.groq.com/v1/chat/completions
  │  │     Prompt: "Review this code..."
  │  ├─ Get analysis response
  │  └─ Store in results
  ├─ Cache results in Redis (for 24 hours)
  └─ Update task status to "SUCCESS"
     │
BROWSER (Polling)
  ↓ GET http://localhost:8000/api/analyze/status/{task_id}
    Header: Authorization: Bearer <token>
  │
FASTAPI (/api/analyze/status/{task_id})
  ├─ Validate token
  └─ GET http://127.0.0.1:8001/task-status/{task_id}/
     Header: Authorization: Bearer <token>
  │
DJANGO (views.py - task_status)
  ├─ Validate token
  ├─ Check Celery task status
  ├─ Get result from Redis cache
  └─ Return: {task_id, status, result}
     │ Status can be: PENDING, SUCCESS, FAILURE
     │ Result contains analysis
     │
FASTAPI
  └─ Return to BROWSER
     │
BROWSER
  ├─ If status = "PENDING" → poll again
  ├─ If status = "SUCCESS" → display results 
  └─ If status = "FAILURE" → show error message
```

---

Django validates token:
  ├─ Decode JWT using SECRET_KEY
  ├─ Check expiry timestamp
  ├─ Extract user_id from payload
  ├─ If valid → process request
  └─ If invalid → return 401

When token expires (30 min):
  BROWSER sends:
    POST /api/auth/refresh
    Body: {refresh_token}
  
  Django generates new access_token
  
  BROWSER updates localStorage
  
  Continue using API 
```

---

## Functionality Flow (What Each Layer Does)

### **Frontend (HTML/CSS/JS)**
- **What**: Static files served by FastAPI
- **Does**:
  - Display login/register forms
  - Collect user input
  - Send HTTP requests
  - Display analysis results
  - Store tokens locally

### **FastAPI (Gateway)**
- **What**: Async HTTP server on port 8000
- **Does**:
  - Receives requests from browser
  - Validates token format
  - Proxies to Django
  - Forwards Authorization header
  - Returns responses to browser

### **Django (Backend)**
- **What**: Web framework with REST API on port 8001
- **Does**:
  - Register users (hash password, save to DB)
  - Login users (verify password, generate JWT)
  - Validate JWT tokens
  - Manage user sessions
  - Create Celery tasks
  - Check task status
  - Return results

### **Celery (Task Queue)**
- **What**: Distributed task processor
- **Does**:
  - Fetch PR files from GitHub
  - Send code to Groq AI
  - Process analysis asynchronously
  - Cache results in Redis
  - Update task status

### **Redis (Cache/Queue)**
- **What**: In-memory data store
- **Does**:
  - Acts as Celery broker (holds tasks)
  - Caches analysis results
  - Stores refresh tokens (optional)

### **Groq AI (LLM)**
- **What**: External AI API
- **Does**:
  - Analyze code
  - Generate insights
  - Return structured JSON

---

##  File Structure & Code Flow

```
django_app/
├── manage.py
├── django_app/
│   ├── settings.py ─────────► JWT config, REST settings
│   ├── urls.py ────────────► Route: /auth/register/ → auth_views.register
│   ├── urls.py ────────────► Route: /start-task/ → views.start_task
│   └── celery.py ──────────► Celery config
│
└── app/
    ├── auth_views.py ──────► register(), login(), get_current_user()
    │                        ├─ Hash password
    │                        ├─ Generate JWT token
    │                        └─ Validate token
    │
    ├── views.py ──────────► start_task(), task_status()
    │                       ├─ Validate token
    │                       ├─ Create Celery task
    │                       └─ Return task status
    │
    └── task.py ───────────► analyze_pr_request()
                           ├─ Fetch GitHub PR files
                           ├─ Call Groq AI
                           ├─ Cache in Redis
                           └─ Return results

fastapi_app/
└── main.py
    ├── /api/auth/register ────┐
    ├── /api/auth/login       |-─ Proxy to Django
    ├── /api/auth/me          │
    ├── /api/auth/refresh ────┘
    │
    ├── /api/analyze/start ────┐
    ├── /api/analyze/status   |-─ Proxy to Django + validate token
    └── /api/analyze/history──┘
```

---

##Complete Request Cycle (Example)

```
1. BROWSER                          6. BROWSER
   POST /api/analyze/start             Check localStorage
   {repo, pr_number}                   Get access_token
        │
        ↓
2. FASTAPI (main.py)
   Extract Authorization header
   Get token from localStorage
        │
        ↓
3. FASTAPI
   GET http://127.0.0.1:8001/auth/me/
   Header: Authorization: Bearer xxx
        │
        ↓
4. DJANGO (auth_views.py)
   jwt.decode(token) → Validate
   Extract user_id → Get user
   Return user_info
        │
        ↓
5. FASTAPI
   POST http://127.0.0.1:8001/start-task/
   Header: Authorization: Bearer xxx 
   Body: {repo, pr_number}
        │
        ↓
6. DJANGO (views.py)
   jwt.decode(token) → Validate
   create Celery task:
     analyze_pr_request.delay(repo, pr_number)
   Return {task_id}
        │
        ↓
7. FASTAPI → BROWSER
   Return task_id
        │
        ↓
8. BROWSER
   Show "Analysis in progress..."
   Poll: GET /api/analyze/status/task_id
   Repeat every 2 seconds
        │
        ↓
9. CELERY (background)
   Fetch GitHub PR files
   Send to Groq AI
   Cache results
        │
        ↓
10. DJANGO (task_status)
    Return status → PENDING or SUCCESS
         │
         ↓
11. BROWSER
    status = SUCCESS → Display results 
```

---

## Running the Application

```bash
# Terminal 1: Django Backend
cd django_app
python manage.py runserver 8001

# Terminal 2: Celery Worker
cd django_app
celery -A django_app.celery worker -l info

# Terminal 3: FastAPI Gateway
cd fastapi_app
uvicorn main:app --reload --port 8000

# Terminal 4: Redis (needed for Celery)
redis-server

# Open browser
http://localhost:8000
```


