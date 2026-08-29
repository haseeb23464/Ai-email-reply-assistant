import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.models import GenerateReplyRequest, GenerateReplyResponse
from backend.llm_service import generate_email_reply

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Email Reply Assistant API")

# Allow the Streamlit frontend (localhost:8501) to call this backend (localhost:8000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Safeguard: override FastAPI's default 422 handler so validation errors
#    return a clean, user-readable message instead of raw Pydantic internals.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return the first human-readable validation message as a simple detail string."""
    errors = exc.errors()
    # Pull the first error's "msg" — Pydantic populates this with our custom
    # ValueError messages from field_validator, or its own built-in messages.
    if errors:
        first = errors[0]
        # Use ctx.error (our ValueError text) if available, else msg.
        msg = first.get("msg", "Invalid input.")
        # Pydantic prefixes custom ValueError messages with "Value error, " — strip it.
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
    else:
        msg = "Invalid input."

    return JSONResponse(status_code=422, content={"detail": msg})


# ── Safeguard: global catch-all for any unhandled exception so the client
#    never sees a raw Python traceback or internal details.
@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.error("Unhandled exception on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


@app.get("/")
def root():
    return {"message": "AI Email Reply Assistant API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/generate-reply", response_model=GenerateReplyResponse)
def generate_reply(request: GenerateReplyRequest):
    """Accept an email and tone, return an AI-generated reply.

    Pydantic validates email_content (non-empty, ≤5000 chars) and tone
    (must be Professional, Friendly, or Short and Concise) before this
    function is called.  Any Gemini errors are caught and returned as a
    generic 500 — raw exception details are logged server-side only.
    """
    try:
        reply_text = generate_email_reply(request.email_content, request.tone)
    except RuntimeError as exc:
        # ── Safeguard: log the real error server-side, return a generic message.
        logger.error("Gemini generation failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate reply. Please try again.",
        )
    except Exception as exc:
        # ── Safeguard: catch ANY unexpected exception (not just RuntimeError)
        #    so a bug in llm_service never leaks internals to the client.
        logger.error("Unexpected error in /generate-reply: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again later.",
        )

    return GenerateReplyResponse(reply=reply_text, tone=request.tone)
