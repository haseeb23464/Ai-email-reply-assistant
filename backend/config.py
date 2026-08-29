import os
import sys

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

# Validate at import time so the app fails fast if the key is missing.
# The key value is never logged or included in any error response.
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    print(
        "ERROR: GEMINI_API_KEY is not set or still has the placeholder value. "
        "Please set a valid key in your .env file.",
        file=sys.stderr,
    )
    sys.exit(1)
