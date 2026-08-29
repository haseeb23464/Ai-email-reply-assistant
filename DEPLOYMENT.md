# 🚀 Deployment Guide

## Why Backend and Frontend Are Deployed Separately

In production, the Streamlit frontend and FastAPI backend run on **different
servers with different public URLs**. They cannot use `localhost` to talk to
each other — `localhost` on a Render server is not the same machine as
`localhost` on a Streamlit Cloud server.

```
Local development                      Production
──────────────────                     ──────────────────────────────────────
Streamlit  → localhost:8000    vs.     Streamlit  → https://my-api.render.com
FastAPI    ← localhost:8501           FastAPI    ← https://my-app.streamlit.app
```

**Rule:** In production, the Streamlit app's `BACKEND_URL` must always be set
to the backend's full public HTTPS URL — never `localhost`.

---

## ⚠️ CORS in Production vs. Development

The backend currently allows all origins (`allow_origins=["*"]`), which is
fine for local development. Before going to production you should tighten this
to your frontend's exact domain so that no other website can call your API.

**Development (`backend/main.py`):**

```python
# Fine for local dev — allows any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    ...
)
```

**Production — replace with the exact frontend URL:**

```python
import os

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8501",  # safe default for local dev
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # e.g. ["https://my-app.streamlit.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Set `ALLOWED_ORIGINS=https://my-app.streamlit.app` in the backend's production
environment variables. Never leave `"*"` open in a deployed API.

---

## Option A — Beginner-Friendly Managed Hosting

Deploy the backend and frontend to free managed platforms with no server
administration required. This is the recommended path for hackathons and MVPs.

### Recommended Platform Pairing

| Service | Platform | Free Tier |
|---------|----------|-----------|
| FastAPI backend | [Render](https://render.com) | ✅ Free web service |
| Streamlit frontend | [Streamlit Community Cloud](https://streamlit.io/cloud) | ✅ Free |

---

### Part 1 — Deploy the FastAPI Backend to Render

#### Step 1 — Prepare a `requirements.txt`

Make sure your `requirements.txt` is committed and up to date. Render uses it
to install dependencies automatically.

```
fastapi>=0.115,<1.0
uvicorn>=0.32,<1.0
pydantic>=2.0,<3.0
python-dotenv>=1.0,<2.0
google-genai>=1.0,<2.0
requests>=2.32,<3.0
httpx>=0.28,<1.0
```

#### Step 2 — Add a `render.yaml` (optional but recommended)

Create `render.yaml` in the project root to codify your Render configuration:

```yaml
services:
  - type: web
    name: ai-email-reply-backend
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GEMINI_API_KEY
        sync: false          # marks this as a secret you enter manually
      - key: GEMINI_MODEL
        value: gemini-2.0-flash
      - key: ALLOWED_ORIGINS
        sync: false          # you will fill this in after the frontend is deployed
```

> **Note on `--port $PORT`:** Render injects a `$PORT` environment variable
> at runtime. Your app must bind to that port, not a hardcoded `8000`.
> The command `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` handles
> this correctly.

#### Step 3 — Push your code to GitHub

```bash
git add .
git commit -m "chore: add render.yaml for backend deployment"
git push origin main
```

#### Step 4 — Create a Render Web Service

1. Go to **[dashboard.render.com](https://dashboard.render.com)** and sign in
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account and select the `ai-email-reply-assistant` repository
4. Fill in the settings:

   | Field | Value |
   |-------|-------|
   | **Name** | `ai-email-reply-backend` |
   | **Region** | Closest to your users |
   | **Branch** | `main` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
   | **Instance Type** | `Free` |

5. Click **"Advanced"** → **"Add Environment Variable"** and add:

   | Key | Value |
   |-----|-------|
   | `GEMINI_API_KEY` | *(paste your actual key — mark as Secret)* |
   | `GEMINI_MODEL` | `gemini-2.0-flash` |
   | `ALLOWED_ORIGINS` | *(leave blank for now — add after frontend is deployed)* |

6. Click **"Create Web Service"**

#### Step 5 — Note your backend's public URL

Once deployed, Render gives you a URL like:

```
https://ai-email-reply-backend.onrender.com
```

**Copy this URL — you will need it in the next section.**

You can verify the backend is live:

```bash
curl https://ai-email-reply-backend.onrender.com/health
# Expected: {"status":"healthy"}
```

---

### Part 2 — Deploy the Streamlit Frontend to Streamlit Community Cloud

#### Step 1 — Ensure `frontend/app.py` reads `BACKEND_URL` from the environment

The frontend already does this correctly:

```python
import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
```

The `"http://127.0.0.1:8000"` default only applies when running locally.
In production, the `BACKEND_URL` secret overrides it.

#### Step 2 — Push the full project to GitHub (if not done already)

```bash
git push origin main
```

Streamlit Community Cloud deploys directly from GitHub — no build scripts
needed.

#### Step 3 — Create a Streamlit Cloud app

1. Go to **[share.streamlit.io](https://share.streamlit.io)** and sign in with
   your Google or GitHub account
2. Click **"New app"**
3. Fill in:

   | Field | Value |
   |-------|-------|
   | **Repository** | `your-username/ai-email-reply-assistant` |
   | **Branch** | `main` |
   | **Main file path** | `frontend/app.py` |
   | **App URL** | Choose a custom slug (e.g. `ai-email-reply`) |

4. Click **"Advanced settings"** and add your secret:

   Under **Secrets**, add the following in TOML format:

   ```toml
   BACKEND_URL = "https://ai-email-reply-backend.onrender.com"
   ```

   This is equivalent to your `.env` file — it is encrypted and never
   committed to your repository.

5. Click **"Deploy!"**

#### Step 4 — Update the backend's `ALLOWED_ORIGINS`

Now that you have your Streamlit app's public URL (e.g.
`https://ai-email-reply.streamlit.app`), go back to Render:

1. Open your backend service → **"Environment"**
2. Set `ALLOWED_ORIGINS` to your Streamlit URL:
   ```
   https://ai-email-reply.streamlit.app
   ```
3. Click **"Save Changes"** — Render will redeploy automatically

#### Step 5 — Verify the full production flow

1. Open your Streamlit app URL in a browser
2. Paste a test email, select a tone, click **Generate Reply**
3. Confirm you receive an AI-generated reply with no errors

If you see a connection error, double-check that `BACKEND_URL` in Streamlit
Secrets matches the exact Render URL (including `https://`).

---

### Part 3 — Production Environment Variable Reference

#### Backend (Render) — Environment Variables

| Variable | Required | Example Value | Notes |
|----------|----------|---------------|-------|
| `GEMINI_API_KEY` | ✅ Yes | `AIzaSy...` | Mark as **Secret** — never paste in plaintext |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Uses this default if unset |
| `ALLOWED_ORIGINS` | ✅ Yes (prod) | `https://ai-email-reply.streamlit.app` | Your Streamlit app's URL |
| `PORT` | Auto | Set by Render | Do not set manually |

#### Frontend (Streamlit Cloud) — Secrets (`secrets.toml` format)

```toml
BACKEND_URL = "https://ai-email-reply-backend.onrender.com"
```

> ⚠️ **Important:** Do not add `GEMINI_API_KEY` to Streamlit secrets. The
> API key must only ever live on the backend. The frontend never needs it.

---

## Option B — Docker Containerization (Future)

This option is **not implemented in the current codebase** and is provided as
a guide for when you want to move beyond free managed hosting or run the app
on your own server (VPS, AWS EC2, etc.).

### Concept

Both services are packaged as Docker images and orchestrated with
Docker Compose or a container platform (Fly.io, Railway, GCP Cloud Run, etc.).

```
docker-compose.yml
├── backend  (Dockerfile.backend)  → image: uvicorn backend.main:app
└── frontend (Dockerfile.frontend) → image: streamlit run frontend/app.py
```

### Backend Dockerfile (example, not yet in repo)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY .env.example .env
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile (example, not yet in repo)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir streamlit requests
COPY frontend/ ./frontend/
EXPOSE 8501
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### `docker-compose.yml` (example)

```yaml
version: "3.8"
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "8501:8501"
    environment:
      - BACKEND_URL=http://backend:8000
    depends_on:
      backend:
        condition: service_healthy
```

> When running inside Docker Compose, the frontend reaches the backend via
> the service name `backend` (Docker's internal DNS), not `localhost`.

---

## 🔒 Security Checklist

Before deploying to any public URL, verify every item below:

- [ ] **`.env` is in `.gitignore`** — run `git ls-files .env` and confirm it
      returns nothing
- [ ] **No API key in source code** — search the repo:
      ```bash
      grep -r "AIzaSy" .
      ```
      This must return no results.
- [ ] **No API key in frontend code** — `frontend/app.py` must not import from
      `backend.config` or reference `GEMINI_API_KEY` in any way
- [ ] **`ALLOWED_ORIGINS` is not `"*"` in production** — wildcard CORS allows
      any website to call your API and consume your Gemini quota
- [ ] **API key is stored as a Secret** in Render (encrypted, not visible in
      logs) — not as a plain environment variable
- [ ] **HTTPS only** — both Render and Streamlit Cloud serve over HTTPS by
      default; never deploy to plain HTTP in production
- [ ] **Rotate the key if ever accidentally exposed** — go to
      [Google AI Studio](https://aistudio.google.com/apikey), delete the
      exposed key, and create a new one
- [ ] **Review Gemini free-tier quotas** — the free tier has rate limits;
      monitor usage in the Google AI Studio dashboard to avoid unexpected
      blocks

---

## 🔁 Redeployment Workflow

After making code changes:

```bash
# 1. Commit and push to GitHub
git add .
git commit -m "fix: describe your change"
git push origin main

# Render: redeploys automatically on push to main
# Streamlit Cloud: redeploys automatically on push to main
```

Both platforms watch your GitHub repository and redeploy within ~1–2 minutes
of a push to `main`. No manual steps required after initial setup.
