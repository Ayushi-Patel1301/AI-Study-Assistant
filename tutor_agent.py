

"""
chattutor.py
=============
This file powers the AI Tutor chat page.
The student types a question, Gemini answers it like a teacher.

How to use in app.py:
    from chattutor import show_ai_tutor
    show_ai_tutor()
"""

import streamlit as st
import google.generativeai as genai
import os
from database import save_message, get_chat_history, clear_chat_history

# ─────────────────────────────────
# SETUP GEMINI
# ─────────────────────────────────

# Load API key from .env file or type it directly here for testing
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_api_key_here")
genai.configure(api_key=GEMINI_API_KEY)

# Create the Gemini model
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction="""
        You are a friendly and helpful AI study tutor for students.
        - Explain concepts simply and clearly
        - Use examples to make things easy to understand
        - If a student is confused, try a different explanation
        - Keep answers focused and not too long
        - Encourage the student when they ask good questions
    """
)


# ─────────────────────────────────
# ASK GEMINI A QUESTION
# ─────────────────────────────────

def ask_gemini(user_id, user_message):
    """
    Send a message to Gemini and get a reply.
    Also loads previous chat so Gemini remembers the conversation.
    """

    # Load old messages from database to give Gemini memory
    old_messages = get_chat_history(user_id)

    # Build chat history in the format Gemini needs
    history = []
    for msg in old_messages:
        history.append({
            "role":  msg["role"],
            "parts": [msg["message"]]
        })

    # Start chat with history
    chat = model.start_chat(history=history)

    # Send the new message and get reply
    response = chat.send_message(user_message)

    return response.text


# ─────────────────────────────────
# THE CHAT PAGE  (Streamlit UI)
# ─────────────────────────────────

def show_ai_tutor():
    st.title("🤖 AI Tutor")
    st.markdown("Ask me anything! I'm here to help you study.")
    st.markdown("---")

    user_id = st.session_state.user_id

    # ── Show chat messages ──────────────────────
    messages = get_chat_history(user_id)

    if not messages:
        st.info("👋 No messages yet. Ask your first question below!")
    else:
        for msg in messages:
            if msg["role"] == "user":
                # Student message — shown on right side
                with st.chat_message("user"):
                    st.write(msg["message"])
            else:
                # AI message — shown on left side
                with st.chat_message("assistant"):
                    st.write(msg["message"])

    # ── Input box at the bottom ─────────────────
    user_input = st.chat_input("Type your question here...")

    if user_input:
        # Show student message immediately
        with st.chat_message("user"):
            st.write(user_input)

        # Save student message to database
        save_message(user_id, "user", user_input)

        # Get Gemini reply
        with st.spinner("Thinking..."):
            try:
                reply = ask_gemini(user_id, user_input)
            except Exception as e:
                reply = f"Sorry, something went wrong: {e}"

        # Show AI reply
        with st.chat_message("assistant"):
            st.write(reply)

        # Save AI reply to database
        save_message(user_id, "assistant", reply)

    # ── Clear chat button ───────────────────────
    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        clear_chat_history(user_id)
        st.success("Chat cleared!")
        st.rerun()