import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Email Reply Assistant", page_icon="✉️", layout="centered")

# ── Header ───────────────────────────────────────────────────────────────────
st.title("✉️ AI Email Reply Assistant")
st.markdown("Paste an email, choose your desired tone, and let AI generate a professional reply.")
st.divider()

# ── Input form ───────────────────────────────────────────────────────────────
email_content = st.text_area(
    "Paste the received email here",
    height=220,
    placeholder=(
        "Hi,\n\n"
        "I wanted to follow up on the project proposal I sent last week. "
        "Could you let me know if the team has had a chance to review it?\n\n"
        "Best regards,\nSarah"
    ),
)

tone = st.selectbox(
    "Choose reply tone",
    options=["Professional", "Friendly", "Short and Concise"],
)

generate_clicked = st.button("Generate Reply", type="primary", use_container_width=True)

# ── Generation logic ─────────────────────────────────────────────────────────
if generate_clicked:
    # ── Safeguard: client-side validation — reject empty / whitespace-only
    #    input immediately so we don't waste a round-trip to the backend.
    if not email_content or not email_content.strip():
        st.error("Please enter an email before generating a reply.")
    else:
        with st.spinner("Generating your reply…"):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/generate-reply",
                    json={"email_content": email_content, "tone": tone},
                    timeout=30,
                )

                if response.status_code == 200:
                    data = response.json()
                    reply = data.get("reply", "")

                    st.divider()
                    st.subheader("Generated Reply")
                    st.info(f"**Tone:** {data.get('tone', tone)}")
                    st.code(reply, language=None)

                elif response.status_code == 422:
                    # ── Safeguard: parse validation detail from the backend's
                    #    custom handler.  Wrap in try/except because the
                    #    response body might not be valid JSON (e.g. if a
                    #    reverse proxy returns an HTML error page).
                    try:
                        detail = response.json().get("detail", "Invalid input.")
                    except (ValueError, KeyError):
                        detail = "Invalid input."
                    st.error(f"Validation error: {detail}")

                else:
                    # ── Safeguard: any other non-200 status.  Parse JSON
                    #    defensively — the response might not be JSON at all.
                    try:
                        detail = response.json().get(
                            "detail", "Something went wrong on the server."
                        )
                    except (ValueError, KeyError):
                        detail = "Something went wrong on the server."
                    st.error(f"Server error ({response.status_code}): {detail}")

            except requests.ConnectionError:
                # ── Safeguard: exact wording from the spec for "backend not running".
                st.error(
                    "Unable to connect to the backend. "
                    "Please make sure the FastAPI server is running."
                )
            except requests.Timeout:
                # ── Safeguard: backend or Gemini took too long.
                st.error(
                    "The request timed out. The server may be overloaded — "
                    "please try again in a moment."
                )
            except Exception:
                # ── Safeguard: catch-all that never prints exc (which could
                #    contain leaked internals like API keys or stack traces).
                st.error(
                    "An unexpected error occurred. Please try again later."
                )
