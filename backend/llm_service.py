import logging

from google import genai

from backend.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

# Initialise the client once at module level for connection reuse.
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = (
    "You are an email reply assistant. Your job is to write a reply to the "
    "email provided by the user.\n\n"
    "Rules:\n"
    "1. Return ONLY the reply text — no explanations, no labels, no markdown fences.\n"
    "2. Match the requested tone exactly.\n"
    "3. Do NOT invent facts, names, dates, or commitments that are not in the original email.\n"
    "4. Do NOT add a 'Subject:' line unless the user explicitly asks for one.\n"
    "5. Keep the reply relevant and concise."
)

# ── Safeguard: cap how long we wait for Gemini so a hung call doesn't block
#    the worker thread indefinitely and starve the server.
GEMINI_TIMEOUT_SECONDS = 30


def generate_email_reply(email_content: str, tone: str) -> str:
    """Call Google Gemini to generate an email reply.

    Args:
        email_content: The original email to reply to.
        tone: The desired tone — Professional, Friendly, or Short and Concise.

    Returns:
        The generated reply text.

    Raises:
        RuntimeError: If the Gemini API call fails or returns empty content.
            The message is safe to log but never contains the API key.
    """
    user_prompt = (
        f"Tone: {tone}\n\n"
        f"Original email:\n"
        f"{email_content}"
    )

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
                # ── Safeguard: per-request timeout so a slow Gemini response
                #    doesn't hang the server thread forever.
                http_options=genai.types.HttpOptions(
                    timeout=GEMINI_TIMEOUT_SECONDS * 1000,  # milliseconds
                ),
            ),
        )

        # ── Safeguard: response.text raises ValueError when the response is
        #    blocked by safety filters.  Catch it explicitly so the user gets
        #    a clean message instead of a traceback.
        try:
            reply_text = response.text
        except ValueError as exc:
            logger.warning("Gemini response blocked by safety filters: %s", exc)
            raise RuntimeError(
                "The AI could not generate a reply for this email. "
                "Try rephrasing the content."
            ) from exc

        if not reply_text or not reply_text.strip():
            raise RuntimeError("Gemini returned an empty response.")

        return reply_text.strip()

    except RuntimeError:
        # Re-raise our own RuntimeErrors as-is (already safe messages).
        raise
    except Exception as exc:
        # ── Safeguard: wrap *any* SDK / network / unexpected error without
        #    leaking raw exception details upstream.  Log the real error
        #    server-side for debugging.
        logger.error("Gemini API call failed: %s", exc, exc_info=True)
        raise RuntimeError(
            "The AI service is temporarily unavailable. Please try again."
        ) from exc
