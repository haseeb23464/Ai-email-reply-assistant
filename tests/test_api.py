import sys
from unittest.mock import patch, MagicMock

# ── Safeguard: mock config before importing anything that touches it, so
#    tests run without a real GEMINI_API_KEY in the environment.
mock_config = MagicMock()
mock_config.GEMINI_API_KEY = "test-key"
mock_config.GEMINI_MODEL = "gemini-2.0-flash"
mock_config.BACKEND_URL = "http://localhost:8000"
sys.modules["backend.config"] = mock_config

# Mock the genai client so importing llm_service doesn't hit the real API.
mock_genai = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = mock_genai

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ── Root & health ────────────────────────────────────────────────────────────

def test_root():
    """GET / returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AI Email Reply Assistant API is running"


def test_health():
    """GET /health returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


# ── Happy path ───────────────────────────────────────────────────────────────

def test_generate_reply_success():
    """POST /generate-reply with valid input returns 200 and a reply."""
    with patch("backend.main.generate_email_reply", return_value="Thanks for your email."):
        response = client.post(
            "/generate-reply",
            json={"email_content": "Hello, how are you?", "tone": "Professional"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Thanks for your email."
    assert data["tone"] == "Professional"


# ── Validation: empty / whitespace ───────────────────────────────────────────

def test_generate_reply_empty_body():
    """POST /generate-reply with empty email_content returns 422."""
    response = client.post(
        "/generate-reply",
        json={"email_content": "", "tone": "Professional"},
    )
    assert response.status_code == 422
    # Custom handler should return the user-friendly message.
    detail = response.json()["detail"]
    assert "email" in detail.lower()


def test_generate_reply_whitespace_only():
    """POST /generate-reply with whitespace-only email_content returns 422
    with the same message as empty input (whitespace is treated as empty)."""
    response = client.post(
        "/generate-reply",
        json={"email_content": "   \n\t  ", "tone": "Friendly"},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "email" in detail.lower()


# ── Validation: invalid tone ────────────────────────────────────────────────

def test_generate_reply_invalid_tone():
    """POST /generate-reply with an invalid tone returns 422."""
    response = client.post(
        "/generate-reply",
        json={"email_content": "Hello", "tone": "Sarcastic"},
    )
    assert response.status_code == 422


# ── Validation: oversized input ─────────────────────────────────────────────

def test_generate_reply_body_too_long():
    """POST /generate-reply with email_content exceeding 5000 chars returns 422."""
    response = client.post(
        "/generate-reply",
        json={"email_content": "A" * 5001, "tone": "Professional"},
    )
    assert response.status_code == 422


# ── Backend / Gemini failures ────────────────────────────────────────────────

def test_generate_reply_gemini_failure():
    """POST /generate-reply returns 500 when Gemini raises RuntimeError."""
    with patch(
        "backend.main.generate_email_reply",
        side_effect=RuntimeError("API quota exceeded"),
    ):
        response = client.post(
            "/generate-reply",
            json={"email_content": "Hello", "tone": "Friendly"},
        )
    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail == "Failed to generate reply. Please try again."
    # ── Safeguard: make sure the raw error message is NOT in the response.
    assert "quota" not in detail.lower()


def test_generate_reply_unexpected_exception():
    """POST /generate-reply returns 500 when an unexpected (non-Runtime)
    exception is raised — verifies the catch-all Exception handler."""
    with patch(
        "backend.main.generate_email_reply",
        side_effect=TypeError("unexpected None"),
    ):
        response = client.post(
            "/generate-reply",
            json={"email_content": "Hello", "tone": "Professional"},
        )
    assert response.status_code == 500
    detail = response.json()["detail"]
    # Should get the generic message, NOT the raw TypeError text.
    assert "unexpected error" in detail.lower()
    assert "None" not in detail


# ── Validation: missing fields entirely ──────────────────────────────────────

def test_generate_reply_missing_email_content():
    """POST /generate-reply with missing email_content field returns 422."""
    response = client.post(
        "/generate-reply",
        json={"tone": "Professional"},
    )
    assert response.status_code == 422


def test_generate_reply_missing_tone():
    """POST /generate-reply with missing tone field returns 422."""
    response = client.post(
        "/generate-reply",
        json={"email_content": "Hello"},
    )
    assert response.status_code == 422


def test_generate_reply_empty_body_json():
    """POST /generate-reply with completely empty JSON body returns 422."""
    response = client.post(
        "/generate-reply",
        json={},
    )
    assert response.status_code == 422
