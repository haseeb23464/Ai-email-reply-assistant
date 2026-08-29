"""
tests/test_api.py
=================
Full test suite for the AI Email Reply Assistant FastAPI backend.

HOW THE MOCK WORKS
------------------
The backend calls `generate_email_reply` from `backend.llm_service`, but
`main.py` imports it with:

    from backend.llm_service import generate_email_reply

That import binds the name `generate_email_reply` inside the `backend.main`
module's own namespace.  If we patched `backend.llm_service.generate_email_reply`
directly we would replace the original object in llm_service, but `main.py`
already holds its own reference to the original function — so the patch would
have no effect on running requests.

The correct target is therefore `backend.main.generate_email_reply` — the name
as it exists *in the module that uses it*.  `unittest.mock.patch` temporarily
replaces that binding for the duration of each `with` block or decorated test,
then restores the original.  This means:

  * No real HTTP call to Gemini is ever made.
  * No GEMINI_API_KEY is required to run the tests.
  * Each test controls exactly what the function returns or raises.

WHY WE ALSO MOCK AT IMPORT TIME
---------------------------------
`backend.config` calls `sys.exit(1)` if `GEMINI_API_KEY` is missing.
`backend.llm_service` instantiates a `genai.Client` at module level.
Both of these happen the moment Python imports the modules — before any test
runs.  We therefore inject fakes into `sys.modules` *before* importing
`backend.main`, so the startup side-effects never execute in the test
environment.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ── Step 1: stub out backend.config ─────────────────────────────────────────
# Replace the real module with a MagicMock so that config.py's sys.exit()
# guard never fires during tests.
_mock_config = MagicMock()
_mock_config.GEMINI_API_KEY = "test-api-key-not-real"
_mock_config.GEMINI_MODEL = "gemini-2.0-flash"
_mock_config.BACKEND_URL = "http://localhost:8000"
sys.modules["backend.config"] = _mock_config

# ── Step 2: stub out google-genai so llm_service's module-level
#    `client = genai.Client(...)` doesn't attempt a real network call.
_mock_google = MagicMock()
_mock_genai = MagicMock()
sys.modules["google"] = _mock_google
sys.modules["google.genai"] = _mock_genai

# ── Step 3: now it is safe to import the app.
from backend.main import app  # noqa: E402  (imports must come after sys.modules patches)

client = TestClient(app)

# ── Shared test data ─────────────────────────────────────────────────────────

VALID_EMAIL = (
    "Hi,\n\n"
    "I wanted to follow up on the project proposal I sent last week. "
    "Could you let me know if the team has had a chance to review it?\n\n"
    "Best regards,\nSarah"
)

VALID_TONES = ["Professional", "Friendly", "Short and Concise"]


# ═══════════════════════════════════════════════════════════════════════════════
# GET /
# ═══════════════════════════════════════════════════════════════════════════════

class TestRootEndpoint:
    def test_returns_200(self):
        """Root endpoint must respond with HTTP 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_returns_expected_message(self):
        """Root response body must contain the exact welcome message."""
        response = client.get("/")
        assert response.json() == {"message": "AI Email Reply Assistant API is running"}

    def test_content_type_is_json(self):
        """Root endpoint must return JSON."""
        response = client.get("/")
        assert "application/json" in response.headers["content-type"]


# ═══════════════════════════════════════════════════════════════════════════════
# GET /health
# ═══════════════════════════════════════════════════════════════════════════════

class TestHealthEndpoint:
    def test_returns_200(self):
        """Health endpoint must respond with HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_returns_healthy_status(self):
        """Health response body must be exactly {"status": "healthy"}."""
        response = client.get("/health")
        assert response.json() == {"status": "healthy"}

    def test_content_type_is_json(self):
        """Health endpoint must return JSON."""
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]


# ═══════════════════════════════════════════════════════════════════════════════
# POST /generate-reply — happy path
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerateReplySuccess:
    """Tests for valid requests that should produce a 200 reply."""

    def test_returns_200_with_valid_input(self):
        """A well-formed request must return HTTP 200."""
        with patch(
            "backend.main.generate_email_reply",
            return_value="Thank you for your email. I will review it shortly.",
        ):
            response = client.post(
                "/generate-reply",
                json={"email_content": VALID_EMAIL, "tone": "Professional"},
            )
        assert response.status_code == 200

    def test_response_contains_reply_field(self):
        """Response body must include a non-empty 'reply' field."""
        expected_reply = "Thank you for your email. I will get back to you soon."
        with patch(
            "backend.main.generate_email_reply",
            return_value=expected_reply,
        ):
            response = client.post(
                "/generate-reply",
                json={"email_content": VALID_EMAIL, "tone": "Professional"},
            )
        data = response.json()
        assert "reply" in data
        assert data["reply"] == expected_reply

    def test_response_contains_tone_field(self):
        """Response body must echo back the tone that was requested."""
        with patch(
            "backend.main.generate_email_reply",
            return_value="Sure thing! Happy to help.",
        ):
            response = client.post(
                "/generate-reply",
                json={"email_content": VALID_EMAIL, "tone": "Friendly"},
            )
        data = response.json()
        assert "tone" in data
        assert data["tone"] == "Friendly"

    @pytest.mark.parametrize("tone", VALID_TONES)
    def test_all_valid_tones_return_200(self, tone):
        """Every accepted tone value must produce HTTP 200."""
        with patch(
            "backend.main.generate_email_reply",
            return_value="This is a reply.",
        ):
            response = client.post(
                "/generate-reply",
                json={"email_content": VALID_EMAIL, "tone": tone},
            )
        assert response.status_code == 200, f"Tone '{tone}' unexpectedly failed"

    def test_mock_is_called_with_correct_arguments(self):
        """The mock records exactly what main.py passes to llm_service."""
        with patch("backend.main.generate_email_reply", return_value="OK") as mock_fn:
            client.post(
                "/generate-reply",
                json={"email_content": VALID_EMAIL, "tone": "Short and Concise"},
            )
        mock_fn.assert_called_once()
        call_args = mock_fn.call_args
        # email_content is the first positional arg; Pydantic strips whitespace.
        assert call_args.args[0] == VALID_EMAIL.strip()
        assert call_args.args[1] == "Short and Concise"

    def test_leading_trailing_whitespace_is_stripped(self):
        """Pydantic strips whitespace before passing to llm_service."""
        padded = "   Hello, please reply.   "
        with patch("backend.main.generate_email_reply", return_value="OK") as mock_fn:
            response = client.post(
                "/generate-reply",
                json={"email_content": padded, "tone": "Professional"},
            )
        assert response.status_code == 200
        # The first arg received by the mock must be stripped.
        assert mock_fn.call_args.args[0] == padded.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# POST /generate-reply — input validation (422 cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerateReplyValidation:
    """All cases where Pydantic should reject the request with 422."""

    # ── email_content ──────────────────────────────────────────────────────

    def test_empty_email_content_returns_422(self):
        """An empty string for email_content must be rejected with 422."""
        response = client.post(
            "/generate-reply",
            json={"email_content": "", "tone": "Professional"},
        )
        assert response.status_code == 422

    def test_empty_email_content_has_readable_detail(self):
        """The 422 detail for an empty email must be a user-readable string,
        not a raw Pydantic error array."""
        response = client.post(
            "/generate-reply",
            json={"email_content": "", "tone": "Professional"},
        )
        body = response.json()
        # Our custom exception handler returns {"detail": "<string>"}.
        assert isinstance(body["detail"], str)
        assert len(body["detail"]) > 0

    def test_whitespace_only_email_returns_422(self):
        """Whitespace-only input is treated as empty and must return 422."""
        response = client.post(
            "/generate-reply",
            json={"email_content": "   \n\t  \n  ", "tone": "Professional"},
        )
        assert response.status_code == 422

    def test_whitespace_only_detail_matches_empty_detail(self):
        """Whitespace-only and empty inputs must produce the same error message
        (both are treated identically by the field_validator)."""
        r_empty = client.post(
            "/generate-reply",
            json={"email_content": "", "tone": "Professional"},
        )
        r_whitespace = client.post(
            "/generate-reply",
            json={"email_content": "   ", "tone": "Professional"},
        )
        assert r_empty.json()["detail"] == r_whitespace.json()["detail"]

    def test_oversized_email_content_returns_422(self):
        """email_content exceeding 5000 characters must return 422."""
        response = client.post(
            "/generate-reply",
            json={"email_content": "A" * 5001, "tone": "Professional"},
        )
        assert response.status_code == 422

    def test_oversized_email_detail_is_readable(self):
        """The 422 detail for an oversized email must mention the limit."""
        response = client.post(
            "/generate-reply",
            json={"email_content": "A" * 5001, "tone": "Professional"},
        )
        detail = response.json()["detail"].lower()
        # Our custom message mentions "5,000" — check for some variant.
        assert "5" in detail and ("000" in detail or "long" in detail or "limit" in detail)

    def test_exactly_5000_chars_is_accepted(self):
        """An email_content of exactly 5000 characters must be accepted (200)."""
        with patch("backend.main.generate_email_reply", return_value="OK"):
            response = client.post(
                "/generate-reply",
                json={"email_content": "B" * 5000, "tone": "Friendly"},
            )
        assert response.status_code == 200

    # ── tone ──────────────────────────────────────────────────────────────

    def test_invalid_tone_returns_422(self):
        """A tone value not in the allowed list must return 422."""
        response = client.post(
            "/generate-reply",
            json={"email_content": VALID_EMAIL, "tone": "Sarcastic"},
        )
        assert response.status_code == 422

    @pytest.mark.parametrize("bad_tone", [
        "professional",          # wrong case
        "FRIENDLY",              # all caps
        "short and concise",     # lowercase
        "Aggressive",            # not in list
        "",                      # empty
        "Professional ",         # trailing space
        " Professional",         # leading space
    ])
    def test_various_invalid_tones_return_422(self, bad_tone):
        """All non-canonical tone strings must be rejected."""
        response = client.post(
            "/generate-reply",
            json={"email_content": VALID_EMAIL, "tone": bad_tone},
        )
        assert response.status_code == 422, (
            f"Expected 422 for tone={bad_tone!r}, got {response.status_code}"
        )

    # ── missing fields ────────────────────────────────────────────────────

    def test_missing_email_content_returns_422(self):
        """A request body with no email_content field must return 422."""
        response = client.post(
            "/generate-reply",
            json={"tone": "Professional"},
        )
        assert response.status_code == 422

    def test_missing_tone_returns_422(self):
        """A request body with no tone field must return 422."""
        response = client.post(
            "/generate-reply",
            json={"email_content": VALID_EMAIL},
        )
        assert response.status_code == 422

    def test_empty_json_body_returns_422(self):
        """A completely empty JSON object must return 422."""
        response = client.post("/generate-reply", json={})
        assert response.status_code == 422

    def test_no_body_returns_422(self):
        """A request with no body at all must return 422."""
        response = client.post("/generate-reply")
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# POST /generate-reply — error handling (500 cases)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerateReplyErrorHandling:
    """Tests verifying that backend errors produce safe, generic 500 responses."""

    def test_gemini_runtime_error_returns_500(self):
        """If generate_email_reply raises RuntimeError, the endpoint returns 500."""
        with patch(
            "backend.main.generate_email_reply",
            side_effect=RuntimeError("Gemini API quota exceeded"),
        ):
            response = client.post(
                "/generate-reply",
                json={"email_content": VALID_EMAIL, "tone": "Friendly"},
            )
        assert response.status_code == 500

    def test_gemini_runtime_error_detail_is_generic(self):
        """The 500 detail must not expose internal error messages like quota info."""
        with patch(
            "backend.main.generate_email_reply",
            side_effect=RuntimeError("API quota exceeded — billing account suspended"),
        ):
            response = client.post(
                "/generate-reply",
                json={"email_content": VALID_EMAIL, "tone": "Friendly"},
            )
        detail = response.json()["detail"]
        # Must be a generic string — raw RuntimeError text must not appear.
        assert "quota" not in detail.lower()
        assert "billing" not in detail.lower()
        assert "suspended" not in detail.lower()

    def test_unexpected_exception_returns_500(self):
        """An unexpected exception (e.g. TypeError) must also return 500,
        not crash the server or expose a traceback."""
        with patch(
            "backend.main.generate_email_reply",
            side_effect=TypeError("unexpected None in pipeline"),
        ):
            response = client.post(
                "/generate-reply",
                json={"email_content": VALID_EMAIL, "tone": "Professional"},
            )
        assert response.status_code == 500

    def test_unexpected_exception_detail_is_generic(self):
        """The 500 detail for an unexpected exception must not leak the TypeError message."""
        with patch(
            "backend.main.generate_email_reply",
            side_effect=TypeError("unexpected None in pipeline"),
        ):
            response = client.post(
                "/generate-reply",
                json={"email_content": VALID_EMAIL, "tone": "Professional"},
            )
        detail = response.json()["detail"]
        assert "None" not in detail
        assert "pipeline" not in detail
        assert "TypeError" not in detail

    def test_500_detail_is_a_string(self):
        """500 responses must return {"detail": "<string>"} — never a raw object."""
        with patch(
            "backend.main.generate_email_reply",
            side_effect=RuntimeError("boom"),
        ):
            response = client.post(
                "/generate-reply",
                json={"email_content": VALID_EMAIL, "tone": "Friendly"},
            )
        body = response.json()
        assert "detail" in body
        assert isinstance(body["detail"], str)

    def test_api_key_never_appears_in_500_response(self):
        """Under no circumstances must the API key value appear in any response."""
        with patch(
            "backend.main.generate_email_reply",
            side_effect=RuntimeError("auth failed for key: test-api-key-not-real"),
        ):
            response = client.post(
                "/generate-reply",
                json={"email_content": VALID_EMAIL, "tone": "Professional"},
            )
        # The mocked key value must not be echoed back.
        assert "test-api-key-not-real" not in response.text
