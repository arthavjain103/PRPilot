# PR Review Project

# Overview

The PR Review System automates code review and repository analysis by fetching pull request files directly from GitHub, sending them through an AI-powered analysis pipeline, and returning meaningful insights about the code. It is built using a microservice-style, decoupled architecture to achieve high performance, scalability, and maintainability. Each service in the system has a specific role and communicates through queues and APIs, ensuring smooth, independent operation without tight coupling. The system combines FastAPI for fast request handling, Django REST Framework for backend logic and task management, Celery + Redis for running background tasks and caching, and Groq LLM for intelligent code understanding and review generation. This architecture ensures that heavy AI processing happens asynchronously, keeping the user experience fast and responsive. Designed for distributed scalability and future extensibility, it reflects real-world enterprise backend design — where every component can scale or update independently for better performance and flexibility.

This repository contains two services used to analyze GitHub pull requests:

- `django_app/` — Django project that fetches PR files and enqueues analysis tasks via Celery.
- `fastapi_app/` — FastAPI service that provides a lightweight HTTP frontend to start tasks and query status.
- `scripts.py` — utility script to call the review API directly (interactive mode).

## 🧱 Architecture Overview

| Layer              | Technology                | Purpose                                                          |
| ------------------ | ------------------------- | ---------------------------------------------------------------- |
| **API Gateway**    | **FastAPI**               | Handles client requests with async I/O for high concurrency      |
| **Core Backend**   | **Django REST Framework** | Manages business logic, user auth, and orchestrates Celery tasks |
| **Task Queue**     | **Celery**                | Executes long-running analysis jobs asynchronously               |
| **Broker & Cache** | **Redis**                 | Acts as Celery broker + caching layer to reduce GitHub API hits  |
| **AI Engine**      | **Groq LLM**              | Performs intelligent code review and insight generation          |
| **External API**   | **GitHub API**            | Fetches pull request data and file contents                      |

### 🧩 Flow Diagram (Conceptual)

```
User → FastAPI → Django (Core API) → Celery → Redis → GitHub API → LLM → Response
```

---

## 🎯 Objectives

- Automate and accelerate PR code review
- Process large GitHub repositories efficiently
- Perform background analysis using Celery
- Use caching to minimize API rate limits
- Generate meaningful insights using AI
- Maintain modular, scalable, future-ready architecture

---

## ⚙️ Why This Architecture?

### ✅ **Microservice-Style Decoupling**

Each component (FastAPI, Django, Celery, Redis, LLM) is independent and can scale separately.
Loose coupling ensures flexibility, faster debugging, and clean code management.

### ⚡ **FastAPI as Gateway**

Handles multiple client requests asynchronously, providing lightning-fast response times even under heavy load.

### 🧠 **Django as Core Logic**

Mature backend for handling authentication, ORM, data validation, and API endpoints — ensuring reliability and security.

### 🔄 **Celery + Redis for Background Processing**

Heavy LLM tasks are offloaded to Celery workers.
Redis acts as both broker and cache — reducing GitHub API load and improving speed.

### 🤖 **LLM Integration Layer**

AI processing is isolated from backend logic, allowing easy model upgrades and parallel experimentation.

### 🌐 **API-Driven Extensibility**

Any frontend (React, CLI, mobile app) can connect through REST APIs — making it a plug-and-play system.

---

## 💡 Why It’s Unique

- Combines **FastAPI** and **Django** in one hybrid system
- True **decoupled microservice design** — not a monolith
- Supports **parallel background AI processing**
- **Extremely modular** — each service can be dockerized and scaled
- Built for **enterprise-grade extensibility** (AI upgrades, new APIs, etc.)

---

## 🧠 Scalability Highlights

- Each layer can scale independently
- Asynchronous FastAPI requests
- Distributed Celery worker pools
- Redis caching to reduce repetitive GitHub requests
- Isolated LLM service = no backend blocking

---

## 🧩 Why Not a Monolith?

| Without This Architecture | Problem                             |
| ------------------------- | ----------------------------------- |
| Single server (monolith)  | Slow, blocked requests              |
| No Celery                 | Long tasks freeze API               |
| No Redis                  | API rate limits hit faster          |
| AI inside backend         | Tight coupling, low maintainability |
| No modularity             | Difficult to scale and debug        |

---

## ✅ Benefits Achieved

- ⚡ High concurrency and low latency
- 🧱 Strong, maintainable backend structure
- 🔄 Seamless background task execution
- 💾 Faster performance via caching
- 🧠 AI analysis integrated safely and asynchronously
- 🚀 Future-ready, horizontally scalable system

---

## 🧰 Tech Stack

- **FastAPI** — API Gateway (async request handling)
- **Django REST Framework** — Business logic & database layer
- **Celery** — Distributed task queue
- **Redis** — Message broker + cache
- **Groq LLM** — AI model for intelligent code review
- **GitHub API** — Data source

---

## ⚙️ Setup (Windows / PowerShell)

### 1️⃣ Environment Setup

```powershell
python -m venv venv
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Or install manually:

```powershell
pip install django celery redis requests httpx groq python-dotenv djangorestframework fastapi uvicorn
```

### 2️⃣ Redis Setup

Ensure Redis server is running on:

```
127.0.0.1:6379
```

### 3️⃣ Environment Variables (`.env`)

```
GROQ_API_KEY=sk_your_groq_key_here
```

---

## 🧩 Running the Services

### **Run Django (Core API)**

```powershell
cd django_app
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### **Run Celery Worker**

```powershell
celery -A django_app.celery worker -l info
```

### **Run FastAPI Gateway**

```powershell
cd fastapi_app
uvicorn main:app --reload --port 8001
```

### **Interactive Script**

```powershell
python scripts.py
```

---

## 🔍 Troubleshooting

| Issue                     | Cause                                                   | Fix                                                 |
| ------------------------- | ------------------------------------------------------- | --------------------------------------------------- |
| `python: can't open file` | Path contains spaces (e.g., `C:\Users\Name With Space`) | Move project to `C:\Projects\PRAnalyzer\`           |
| `Celery module not found` | Wrong app path                                          | Use `celery -A django_app.celery worker -l info`    |
| `RLock not greened`       | Eventlet not patched                                    | Add `eventlet.monkey_patch()` at top of `celery.py` |

---

## 🧩 Future Enhancements

- 🪶 Add PostgreSQL for persistent result storage
- 🧩 Integrate WebSocket (real-time task progress)
- 💬 Add frontend layer

---

## 📡 API Routes

Below are the main routes provided by the two services. Example payloads and example responses are included.

### FastAPI (gateway)

- POST /start-task
  - Description: Forwards a request to Django to start analysis on a PR.
  - Body (JSON):

```json
{
  "repo_url": "https://github.com/<owner>/<repo>",
  "pr_number": "123",
  "github_token": "<optional_token>"
}
```

    - Response (example):

```json
{
  "task_id": "a1b2c3...",
  "status": "task started"
}
```

- GET /task-status/{task_id}/
  - Description: Forwards request to Django to fetch Celery task status and result.
  - Response (example):

```json
{
	"task_id": "a1b2c3...",
	"status": "SUCCESS",
	"result": {
		"task_id ": "...",
		"analysis_result": [
			{"filename": "src/Pages/Privacy.jsx", "analysis_result": {...}}
		]
	}
}
```

