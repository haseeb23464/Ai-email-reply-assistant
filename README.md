# ✉️ AI Email Reply Assistant

> Paste any email you received, pick a reply tone, and get a polished AI-written reply in seconds — powered by Google Gemini.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.45%2B-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-2.0%20Flash-4285F4?logo=google)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Folder Structure](#-folder-structure)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Set Up a Virtual Environment](#2-set-up-a-virtual-environment)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Configure Environment Variables](#4-configure-environment-variables)
  - [5. Get a Gemini API Key](#5-get-a-gemini-api-key)
- [Running the App](#-running-the-app)
  - [Start the FastAPI Backend](#start-the-fastapi-backend)
  - [Start the Streamlit Frontend](#start-the-streamlit-frontend)
  - [One-Command Launch (Both Servers)](#one-command-launch-both-servers)
- [Swagger API Docs](#-swagger-api-docs)
- [API Endpoint Reference](#-api-endpoint-reference)
- [Example Usage](#-example-usage)
- [Running Tests](#-running-tests)
- [Error Handling Summary](#-error-handling-summary)
- [GitHub Setup](#-github-setup)
- [Deployment](#-deployment)
- [Future Improvements](#-future-improvements)
- [Author](#-author)

---

## ✨ Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Email Input** | Paste any received email into a large text area |
| 2 | **Tone Selection** | Choose from *Professional*, *Friendly*, or *Short and Concise* |
| 3 | **AI Reply Generation** | One click generates a polished reply via Google Gemini |

**What this project does NOT do** (by design — keep it simple):
- No user accounts or authentication
- No database or stored history
- No actual email sending
- No LangChain, RAG, or chat history

---

## 🏗️ System Architecture

```
┌───────────────────────┐         HTTP (port 8000)        ┌───────────────────────┐
│                       │  POST /generate-reply           │                       │
│   Streamlit Frontend  │ ──────────────────────────────► │   FastAPI Backend     │
│   (localhost:8501)    │                                 │   (localhost:8000)    │
│                       │ ◄────────── JSON ────────────── │                       │
└───────────────────────┘                                 └──────────┬────────────┘
                                                                     │
                                                          google-genai SDK
                                                                     │
                                                                     ▼
                                                          ┌──────────────────────┐
                                                          │   Google Gemini API  │
                                                          │  (gemini-2.0-flash)  │
                                                          └──────────────────────┘
```

**Data flow:**
1. User pastes an email and selects a tone in the Streamlit UI
2. Streamlit sends `POST /generate-reply` to the FastAPI backend
3. FastAPI validates the request with Pydantic models
4. FastAPI calls Google Gemini via the `google-genai` SDK
5. Gemini returns generated reply text
6. FastAPI returns `{"reply": "...", "tone": "..."}` to Streamlit
7. Streamlit displays the reply in a copyable code block

> **The frontend never touches the Gemini API or the API key directly.**

---

## 📁 Folder Structure

```
ai-email-reply-assistant/
│
├── backend/
│   ├── __init__.py          # Package marker
│   ├── main.py              # FastAPI app, routes, error handlers
│   ├── models.py            # Pydantic request/response models
│   ├── llm_service.py       # Google Gemini API integration
│   └── config.py            # Environment variable loading & validation
│
├── frontend/
│   └── app.py               # Streamlit UI
│
├── tests/
│   ├── __init__.py          # Package marker
│   └── test_api.py          # pytest test suite (32 tests, no API key needed)
│
├── .env                     # Your local secrets (gitignored)
├── .env.example             # Template — copy this to .env
├── .gitignore               # Ignores .env, venv, __pycache__, etc.
├── requirements.txt         # All Python dependencies
├── run.py                   # Convenience launcher for both servers
├── SPEC.md                  # Full technical specification
└── README.md                # This file
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | [Streamlit](https://streamlit.io/) | Single-page web UI |
| **Frontend** | [requests](https://docs.python-requests.org/) | HTTP client to call the backend |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) | REST API framework |
| **Backend** | [Uvicorn](https://www.uvicorn.org/) | ASGI server |
| **Backend** | [Pydantic v2](https://docs.pydantic.dev/) | Request/response validation |
| **Backend** | [google-genai](https://pypi.org/project/google-genai/) | Google Gemini SDK |
| **Backend** | [python-dotenv](https://pypi.org/project/python-dotenv/) | `.env` file loading |
| **Testing** | [pytest](https://pytest.org/) | Test runner |
| **Testing** | [httpx](https://www.python-httpx.org/) | Async HTTP client (TestClient dep) |
| **Runtime** | Python 3.10+ | Language |
| **AI Model** | Gemini 2.0 Flash | Reply generation |

---

## 📦 Prerequisites

Before you begin, make sure you have:

- **Python 3.10 or newer** — [Download](https://www.python.org/downloads/)
- **Git** — [Download](https://git-scm.com/downloads)
- A **Google account** to get a free Gemini API key
- A terminal: **PowerShell** (Windows) or **Terminal** (macOS/Linux)

Verify your Python version:

```powershell
# Windows PowerShell
python --version
```

```bash
# macOS / Linux
python3 --version
```

---

## 🚀 Installation

### 1. Clone the Repository

```powershell
# Windows PowerShell
git clone https://github.com/<your-username>/ai-email-reply-assistant.git
cd ai-email-reply-assistant
```

```bash
# macOS / Linux
git clone https://github.com/<your-username>/ai-email-reply-assistant.git
cd ai-email-reply-assistant
```

---

### 2. Set Up a Virtual Environment

A virtual environment keeps this project's packages isolated from your system Python.

```powershell
# Windows PowerShell — create the environment
python -m venv .venv

# Activate it
.venv\Scripts\Activate.ps1
```

> **PowerShell execution policy error?** Run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

```bash
# macOS / Linux — create and activate
python3 -m venv .venv
source .venv/bin/activate
```

You should now see `(.venv)` at the start of your terminal prompt.

---

### 3. Install Dependencies

```powershell
# Windows PowerShell
pip install -r requirements.txt
```

```bash
# macOS / Linux
pip install -r requirements.txt
```

This installs all packages needed for the backend, frontend, and tests.

---

### 4. Configure Environment Variables

Copy the example file to create your local `.env`:

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

```bash
# macOS / Linux
cp .env.example .env
```

Open `.env` in any text editor and fill in your values:

```env
GEMINI_API_KEY=your_actual_api_key_here
BACKEND_URL=http://127.0.0.1:8000
```

> ⚠️ **Never commit `.env` to Git.** It is already listed in `.gitignore`.

---

### 5. Get a Gemini API Key

1. Go to **[Google AI Studio](https://aistudio.google.com/apikey)**
2. Sign in with your Google account
3. Click **"Create API key"**
4. Copy the key and paste it into your `.env` file as `GEMINI_API_KEY`

The free tier is sufficient for development and testing.

---

## ▶️ Running the App

You need **two terminal windows** — one for the backend and one for the frontend.

### Start the FastAPI Backend

```powershell
# Windows PowerShell (Terminal 1) — make sure .venv is active
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
# macOS / Linux (Terminal 1)
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

---

### Start the Streamlit Frontend

```powershell
# Windows PowerShell (Terminal 2) — make sure .venv is active
streamlit run frontend/app.py --server.port 8501
```

```bash
# macOS / Linux (Terminal 2)
streamlit run frontend/app.py --server.port 8501
```

Then open your browser at **[http://localhost:8501](http://localhost:8501)**.

---

### One-Command Launch (Both Servers)

Prefer a single command? Use the included convenience launcher:

```powershell
# Windows PowerShell — starts backend then frontend
python run.py
```

```bash
# macOS / Linux
python run.py
```

You can also start servers individually:

```powershell
python run.py backend    # backend only
python run.py frontend   # frontend only
```

---

## 📖 Swagger API Docs

FastAPI generates interactive documentation automatically.

| Interface | URL |
|-----------|-----|
| **Swagger UI** (interactive) | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| **ReDoc** (readable) | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) |
| **OpenAPI JSON** | [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) |

You can test the `/generate-reply` endpoint directly from the Swagger UI without needing the frontend.

---

## 📡 API Endpoint Reference

### `GET /`

Returns a confirmation message that the API is running.

**Response `200 OK`:**
```json
{
  "message": "AI Email Reply Assistant API is running"
}
```

---

### `GET /health`

Lightweight health check for readiness probes.

**Response `200 OK`:**
```json
{
  "status": "healthy"
}
```

---

### `POST /generate-reply`

Accepts an email and tone, returns an AI-generated reply.

**Request body:**

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `email_content` | `string` | ✅ | Non-empty, max 5,000 characters |
| `tone` | `string` | ✅ | Exactly one of: `Professional`, `Friendly`, `Short and Concise` |

**Request:**
```json
{
  "email_content": "Hi,\n\nI wanted to follow up on the project proposal I sent last week. Could you let me know if the team has had a chance to review it?\n\nBest regards,\nSarah",
  "tone": "Professional"
}
```

**Response `200 OK`:**
```json
{
  "reply": "Dear Sarah,\n\nThank you for following up. The team has had a chance to review your proposal and we are very impressed with the direction you've outlined. I would be happy to schedule a meeting to discuss next steps — would Thursday at 2:00 PM work for you?\n\nBest regards",
  "tone": "Professional"
}
```

**Response `422 Unprocessable Entity`** (validation failure):
```json
{
  "detail": "Please enter an email before generating a reply."
}
```

**Response `500 Internal Server Error`** (Gemini failure):
```json
{
  "detail": "Failed to generate reply. Please try again."
}
```

---

## 💡 Example Usage

### From the UI

1. Open **[http://localhost:8501](http://localhost:8501)**
2. Paste a received email into the text area
3. Select a tone from the dropdown
4. Click **Generate Reply**
5. Copy the result from the output box

### From the Command Line (curl)

```powershell
# Windows PowerShell
curl -X POST "http://127.0.0.1:8000/generate-reply" `
  -H "Content-Type: application/json" `
  -d '{"email_content": "Hi, can we reschedule our meeting?", "tone": "Friendly"}'
```

```bash
# macOS / Linux
curl -X POST "http://127.0.0.1:8000/generate-reply" \
  -H "Content-Type: application/json" \
  -d '{"email_content": "Hi, can we reschedule our meeting?", "tone": "Friendly"}'
```

### From Python (requests)

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/generate-reply",
    json={
        "email_content": "Hi, can we reschedule our meeting?",
        "tone": "Friendly",
    },
)
print(response.json()["reply"])
```

---

## 🧪 Running Tests

The test suite has **32 tests** and requires **no real Gemini API key** — all calls to Gemini are mocked.

```powershell
# Windows PowerShell — run all tests
pytest tests/ -v
```

```bash
# macOS / Linux
pytest tests/ -v
```

**Run a specific test class:**

```powershell
pytest tests/test_api.py::TestGenerateReplyValidation -v
```

**Run tests matching a keyword:**

```powershell
pytest tests/ -v -k "tone"
```

**Run with coverage** (requires `pytest-cov`):

```powershell
pip install pytest-cov
pytest tests/ -v --cov=backend --cov-report=term-missing
```

**Expected output:**

```
tests/test_api.py::TestRootEndpoint::test_returns_200                         PASSED
tests/test_api.py::TestRootEndpoint::test_returns_expected_message            PASSED
tests/test_api.py::TestHealthEndpoint::test_returns_200                       PASSED
tests/test_api.py::TestHealthEndpoint::test_returns_healthy_status            PASSED
tests/test_api.py::TestGenerateReplySuccess::test_returns_200_with_valid_input PASSED
...
32 passed in 1.23s
```

---

## 🛡️ Error Handling Summary

| Scenario | Where caught | User sees |
|----------|-------------|-----------|
| Empty email input | Streamlit (client-side) | `"Please enter an email before generating a reply."` |
| Whitespace-only input | Pydantic validator (server-side) | Same as empty |
| Email over 5,000 characters | Pydantic validator | `"Email content is too long. Please limit it to 5,000 characters."` |
| Invalid tone value | Pydantic `Literal` type | `422` with readable message |
| Missing request fields | Pydantic (server-side) | `422` with readable message |
| Backend not running | Streamlit `ConnectionError` | `"Unable to connect to the backend. Please make sure the FastAPI server is running."` |
| Request timeout | Streamlit `Timeout` | `"The request timed out. Please try again in a moment."` |
| Gemini API error / quota | `llm_service.py` → `RuntimeError` | `"Failed to generate reply. Please try again."` |
| Gemini safety filter block | `llm_service.py` `ValueError` | `"The AI could not generate a reply for this email."` |
| Any unexpected server error | Global exception handler | `"An unexpected error occurred. Please try again later."` |

> **The API key, stack traces, and raw exception messages are never exposed to the client.**

---

## 🐙 GitHub Setup

### Initialize a new repository

```powershell
# Windows PowerShell — inside the project folder
git init
git add .
git commit -m "feat: initial project scaffolding"
```

### Connect to GitHub

```powershell
git remote add origin https://github.com/<your-username>/ai-email-reply-assistant.git
git branch -M main
git push -u origin main
```

### Verify .env is not tracked

```powershell
# This should show nothing — if it does, remove .env from git
git ls-files .env
```

### Recommended branch workflow

```powershell
# Create a feature branch
git checkout -b feat/your-feature-name

# After making changes
git add .
git commit -m "feat: describe your change"
git push origin feat/your-feature-name

# Open a Pull Request on GitHub, then merge to main
```

---

## ☁️ Deployment

### Local (Development)

Follow the [Running the App](#-running-the-app) section above. This is the recommended approach for the hackathon.

### Docker Compose (Optional)

Build and run both services in containers:

```powershell
# Windows PowerShell — build and start
docker compose up --build
```

```bash
# macOS / Linux
docker compose up --build
```

This uses the `docker-compose.yml` configuration to:
- Expose the backend on port `8000`
- Expose the frontend on port `8501`
- Pass your `.env` file to the backend container

Stop both containers:

```powershell
docker compose down
```

### Cloud Options (Post-Hackathon)

| Service | What to deploy | Notes |
|---------|---------------|-------|
| **Railway** | Backend (FastAPI) | Set `GEMINI_API_KEY` as a secret env var |
| **Render** | Backend (FastAPI) | Free tier available |
| **Streamlit Community Cloud** | Frontend (Streamlit) | Free; set `BACKEND_URL` in Secrets |
| **Hugging Face Spaces** | Frontend (Streamlit) | Free; supports Streamlit natively |

For cloud deployment, set `BACKEND_URL` in the frontend environment to point to your deployed backend URL (not `localhost`).

---

## 🔮 Future Improvements

These features are intentionally out of scope for the MVP but could be added:

- [ ] **Copy to clipboard button** — one-click copy instead of selecting from code block
- [ ] **Custom tone** — free-text tone input in addition to the three presets
- [ ] **Reply length control** — short / medium / long slider
- [ ] **Multi-language support** — reply in a different language than the input
- [ ] **Email thread context** — paste multiple emails for a more contextual reply
- [ ] **Export options** — download reply as `.txt` or copy as formatted HTML
- [ ] **Dark / light theme toggle** — Streamlit theme selector
- [ ] **Rate limiting** — per-IP request throttling on the backend
- [ ] **Usage analytics** — anonymous request count dashboard
- [ ] **Docker multi-stage build** — smaller production images

---

## 👥 Authors

**Talha Muhammad Haseeb**
- Linkedin : https://www.linkedin.com/in/talha-muhammed-haseeb-711653397
- GitHub: [@haseeb23464](https://github.com/haseeb23464)
- Email : haseeb.23464@gmail.com

**Zeeshan Ali**
- Linkedin : https://www.linkedin.com/in/zeeshan-ali11/
- GitHub: [@z-shan-code](https://github.com/z-shan-code)
- Email : zeeshan.work191@gmail.com 

**Amar Shairwan**
- Linkedin : https://www.linkedin.com/in/amarshairwan
- GitHub: [@Amar-Ai01](https://github.com/Amar-Ai01)
- Email : sharidev66@gmail.com

Built as a mini-hackathon project to demonstrate a clean Streamlit → FastAPI → Gemini architecture. See [SPEC.md](SPEC.md) for the full technical specification.

---

*Made with ❤️ and a lot of emails that needed better replies.*
