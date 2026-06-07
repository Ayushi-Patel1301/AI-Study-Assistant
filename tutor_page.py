# import streamlit as st
# from tutor_agent import TutorAgent

# def show():
#     agent=TutorAgent()
#     st.title("🤖 AI Tutor")

#     # ---------------- CHAT HISTORY ----------------
#     if "chat" not in st.session_state:
#         st.session_state.chat = []

#     # ---------------- DISPLAY CHAT ----------------
#     for role, msg in st.session_state.chat:
#         if role == "user":
#             st.chat_message("user").write(msg)
#         else:
#             st.chat_message("assistant").write(msg)

#     # ---------------- INPUT ----------------
#     user_input = st.chat_input("Ask your question...")

#     if user_input:

#         # Save user message
#         st.session_state.chat.append(("user", user_input))

#         # Get AI response
#         # response = agent.get_response( user_input )

# try:
#     response = agent.get_response(user_input)
# except Exception:
#     response = "⚠️ Something went wrong. Please try again."

#         # Save AI response
#         st.session_state.chat.append(("assistant", response))

#         # Rerun to refresh UI
#         st.rerun()



import streamlit as st
from tutor_agent import TutorAgent

def show():

    agent = TutorAgent()
    st.title("🤖 AI Tutor")

    # ---------------- CHAT HISTORY ----------------
    if "chat" not in st.session_state:
        st.session_state.chat = []

    # ---------------- DISPLAY CHAT ----------------
    for role, msg in st.session_state.chat:
        if role == "user":
            st.chat_message("user").write(msg)
        else:
            st.chat_message("assistant").write(msg)

    # ---------------- INPUT ----------------
    user_input = st.chat_input("Ask your question...")

    if user_input:

        # Save user message
        st.session_state.chat.append(("user", user_input))

        # Get AI response safely
        try:
            response = agent.get_response(user_input)
        except Exception:
            response = "⚠️ AI is busy or something went wrong. Please try again."

        # Save AI response
        st.session_state.chat.append(("assistant", response))

        # Refresh UI
        st.rerun()