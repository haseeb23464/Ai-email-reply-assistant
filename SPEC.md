# AI Email Reply Assistant

## Project Name

**AI Email Reply Assistant** — A lightweight web application that generates AI-powered email replies with selectable tone using Google Gemini.

---

## Problem Statement

Composing professional or context-appropriate email replies is time-consuming and mentally draining, especially for students and early-career professionals who may struggle with tone and phrasing. Users need a fast, zero-friction tool that takes a received email and produces a well-written reply in their desired tone — without signing up, installing anything, or managing conversation history.

---

## Target Users

- **Students** participating in hackathons or learning to build full-stack AI apps
- **Professionals** who want a quick draft reply to common emails
- **Non-native English speakers** who need help composing natural-sounding replies

---

## MVP Scope

The MVP delivers exactly **three features**:

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Email Input** | A text area where the user pastes the email they received. |
| 2 | **Tone Selection** | A selector offering three tones: *Professional*, *Friendly*, *Short and Concise*. |
| 3 | **AI Reply Generation** | A button that sends the email and selected tone to the backend, which calls Google Gemini and returns a generated reply displayed on screen. |

---

## Out of Scope

The following are explicitly **not** part of this project:

- User authentication or accounts
- Database or any form of persistence
- Actual email sending (SMTP, Gmail API, etc.)
- Retrieval-Augmented Generation (RAG)
- LangChain or any orchestration framework
- Chat history or multi-turn conversation
- File attachments or rich-text email parsing
- Rate limiting or usage quotas
- Deployment to production cloud infrastructure (beyond local Docker)

---

## Tech Stack

### Backend

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework for the REST API |
| `uvicorn` | ASGI server to run FastAPI |
| `pydantic` | Request/response validation and serialization |
| `google-genai` | Official Google Generative AI SDK for Gemini |
| `python-dotenv` | Load environment variables from `.env` file |

### Frontend

| Package | Purpose |
|---------|---------|
| `streamlit` | UI framework for the single-page web app |
| `requests` | HTTP client to call the FastAPI backend |

### Testing

| Package | Purpose |
|---------|---------|
| `pytest` | Test runner and framework |
| `httpx` | Async-compatible HTTP client for FastAPI `TestClient` |

### Runtime

- **Python**: 3.10+
- **Gemini Model**: `gemini-2.0-flash` (or latest available flash model)

---

## System Architecture

```
┌───────────────────────┐       HTTP        ┌───────────────────────┐       SDK        ┌──────────────┐
│                       │   POST /generate  │                       │   generateContent │              │
│   Streamlit Frontend  │ ──────-reply────► │   FastAPI Backend     │ ────────────────► │  Gemini API  │
│   (localhost:8501)    │                   │   (localhost:8000)    │                   │              │
│                       │ ◄──── JSON ────── │                       │ ◄──── response ── │              │
└───────────────────────┘                   └───────────────────────┘                   └──────────────┘
```

### Data Flow

1. User pastes an email into the Streamlit text area.
2. User selects a reply tone from the dropdown.
3. User clicks **"Generate Reply"**.
4. Streamlit sends a `POST` request to `http://localhost:8000/generate-reply` with the email body and tone.
5. FastAPI validates the request using Pydantic models.
6. FastAPI constructs a prompt and calls the Gemini API via the `google-genai` SDK.
7. Gemini returns the generated reply text.
8. FastAPI wraps the reply in a JSON response and sends it back to Streamlit.
9. Streamlit displays the generated reply to the user.

> [!IMPORTANT]
> The frontend **never** calls the Gemini API directly. All AI calls are proxied through the FastAPI backend.

---

## API Specification

### `GET /`

**Root endpoint** — returns a welcome message confirming the API is running.

**Response** `200 OK`

```json
{
  "message": "Welcome to the AI Email Reply Assistant API"
}
```

---

### `GET /health`

**Health check** — used for readiness/liveness probes.

**Response** `200 OK`

```json
{
  "status": "healthy"
}
```

---

### `POST /generate-reply`

**Core endpoint** — accepts an email body and desired tone, returns an AI-generated reply.

#### Request Body

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `email_body` | `string` | Yes | Non-empty, max 5,000 characters |
| `tone` | `string` | Yes | One of: `Professional`, `Friendly`, `Short and Concise` |

#### Example Request

```json
{
  "email_body": "Hi,\n\nI wanted to follow up on the project proposal I sent last week. Could you let me know if the team has had a chance to review it? I'd love to schedule a meeting to discuss next steps.\n\nBest regards,\nSarah",
  "tone": "Professional"
}
```

#### Example Response `200 OK`

```json
{
  "reply": "Dear Sarah,\n\nThank you for following up. I can confirm that the team has reviewed your proposal and we are impressed with the direction you've outlined. I would be happy to schedule a meeting to discuss next steps — would Thursday at 2:00 PM work for you?\n\nPlease let me know your availability and I will send a calendar invite.\n\nBest regards"
}
```

#### Error Response `422 Unprocessable Entity`

```json
{
  "detail": [
    {
      "loc": ["body", "tone"],
      "msg": "Input should be 'Professional', 'Friendly' or 'Short and Concise'",
      "type": "literal_error"
    }
  ]
}
```

#### Error Response `500 Internal Server Error`

```json
{
  "detail": "Failed to generate reply. Please try again."
}
```

---

## Environment Variables

All environment variables are loaded from a `.env` file in the project root using `python-dotenv`.

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key obtained from [Google AI Studio](https://aistudio.google.com/apikey) | `AIzaSy...` |
| `BACKEND_URL` | No | URL of the FastAPI backend (used by Streamlit frontend) | `http://localhost:8000` (default) |

### `.env.example`

```env
GEMINI_API_KEY=your_gemini_api_key_here
BACKEND_URL=http://localhost:8000
```

> [!CAUTION]
> Never commit your `.env` file. Ensure `.env` is listed in `.gitignore`.

---

## Validation Rules

### Request Validation (Pydantic)

| Field | Rule | Error Behavior |
|-------|------|----------------|
| `email_body` | Must be a non-empty string | Returns `422` with field-level error |
| `email_body` | Must not exceed 5,000 characters | Returns `422` with field-level error |
| `email_body` | Leading/trailing whitespace is stripped before validation | — |
| `tone` | Must be one of: `Professional`, `Friendly`, `Short and Concise` | Returns `422` with literal error |

### Pydantic Model

```python
from pydantic import BaseModel, Field
from typing import Literal

class ReplyRequest(BaseModel):
    email_body: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The email content to reply to"
    )
    tone: Literal["Professional", "Friendly", "Short and Concise"] = Field(
        ...,
        description="The desired tone of the reply"
    )

class ReplyResponse(BaseModel):
    reply: str = Field(
        ...,
        description="The AI-generated email reply"
    )
```

---

## Error Handling

| Scenario | HTTP Status | Response Body | Handling |
|----------|-------------|---------------|----------|
| Missing or invalid fields in request | `422` | Pydantic validation errors (auto-generated by FastAPI) | Automatic via FastAPI |
| `GEMINI_API_KEY` not set | `500` | `{"detail": "Server configuration error. Please contact the administrator."}` | Check at startup; raise `HTTPException` at request time if missing |
| Gemini API call fails (network, quota, etc.) | `500` | `{"detail": "Failed to generate reply. Please try again."}` | Catch exceptions from `google-genai`, log the error, return generic message |
| Gemini returns empty response | `500` | `{"detail": "Failed to generate reply. Please try again."}` | Check for empty/null content before returning |
| Backend unreachable from frontend | — | Streamlit shows user-friendly error: *"Could not connect to the backend. Make sure the API server is running."* | `try/except` around `requests.post()` in Streamlit |

> [!NOTE]
> Internal error details (stack traces, Gemini error messages) are **logged server-side only** and never exposed to the client.

---

## Testing Strategy

### Unit Tests (Backend)

Use `pytest` with FastAPI's `TestClient` (powered by `httpx`).

| Test Case | Description |
|-----------|-------------|
| `test_root` | `GET /` returns `200` with welcome message |
| `test_health` | `GET /health` returns `200` with `{"status": "healthy"}` |
| `test_generate_reply_success` | `POST /generate-reply` with valid input returns `200` and a non-empty `reply` field (mock Gemini) |
| `test_generate_reply_empty_body` | `POST /generate-reply` with empty `email_body` returns `422` |
| `test_generate_reply_invalid_tone` | `POST /generate-reply` with invalid tone returns `422` |
| `test_generate_reply_body_too_long` | `POST /generate-reply` with `email_body` exceeding 5,000 chars returns `422` |
| `test_generate_reply_gemini_failure` | `POST /generate-reply` where Gemini call raises an exception returns `500` (mock Gemini to raise) |

### Mocking Strategy

- **Mock the Gemini API** using `unittest.mock.patch` to avoid real API calls and API key requirements during testing.
- Tests must be runnable without a valid `GEMINI_API_KEY`.

### Running Tests

```bash
pytest tests/ -v
```

---

## Deployment Plan

### Local Development (Primary)

This project is designed to run locally during the hackathon.

#### 1. Clone and install dependencies

```bash
git clone <repository-url>
cd ai-email-reply-assistant

# Backend
pip install -r requirements.txt

# Frontend (if separate requirements file)
pip install -r requirements-frontend.txt
```

#### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

#### 3. Start the backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. Start the frontend (in a separate terminal)

```bash
streamlit run app.py --server.port 8501
```

#### 5. Open the app

Navigate to `http://localhost:8501` in your browser.

### Project Structure

```
ai-email-reply-assistant/
├── backend/
│   ├── main.py              # FastAPI app with all endpoints
│   ├── models.py            # Pydantic request/response models
│   ├── gemini_service.py    # Gemini API integration
│   └── requirements.txt     # Backend dependencies
├── frontend/
│   ├── app.py               # Streamlit UI
│   └── requirements.txt     # Frontend dependencies
├── tests/
│   ├── __init__.py
│   └── test_api.py          # API endpoint tests
├── .env.example             # Template for environment variables
├── .gitignore               # Includes .env
├── SPEC.md                  # This specification document
└── README.md                # Setup and usage instructions
```

### Optional: Docker Compose

For simplified multi-service startup:

```yaml
version: "3.8"
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
  frontend:
    build: ./frontend
    ports:
      - "8501:8501"
    environment:
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend
```

> [!TIP]
> Docker is optional for the hackathon. Running the backend and frontend in two separate terminals is the fastest way to get started.
