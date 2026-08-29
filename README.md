# AI Email Reply Assistant

Paste an email you received, pick a reply tone, and get an AI-written reply powered by Google Gemini.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your Gemini API key from https://aistudio.google.com/apikey
```

### 3. Run the app

**Both servers at once:**

```bash
python run.py
```

**Or separately:**

```bash
# Terminal 1 — Backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
streamlit run frontend/app.py --server.port 8501
```

### 4. Open the app

Navigate to [http://localhost:8501](http://localhost:8501) in your browser.

## Run Tests

```bash
pytest tests/ -v
```

## Tech Stack

| Layer | Packages |
|-------|----------|
| Backend | FastAPI, Uvicorn, Pydantic, google-genai, python-dotenv |
| Frontend | Streamlit, Requests |
| Testing | pytest, httpx |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Welcome message |
| GET | `/health` | Health check |
| POST | `/generate-reply` | Generate an AI email reply |

See [SPEC.md](SPEC.md) for the full technical specification.
