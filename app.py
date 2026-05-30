from chat_tutor import show_ai_tutor
from chat_tutor import show_dashboard
from chat_tutor import show_pdf_assistant
from chat_tutor import show_ai_tutor
from chat_tutor import show_ai_tutor
from chat_tutor import show_ai_tutor








"""
app.py
=======
This is the main file of the app.
Run it with:  streamlit run app.py

It handles:
- Login and Register pages
- Sidebar navigation
- Dark theme
- Routing to other pages
"""

import streamlit as st
from database import create_tables, register_user, login_user

# ─────────────────────────────────
# PAGE SETUP  (must be first!)
# ─────────────────────────────────

st.set_page_config(
    page_title="AI Study Platform",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────
# DARK THEME STYLE
# ─────────────────────────────────

st.markdown("""
    <style>
        /* Main background */
        .stApp {
            background-color: #0E1117;
            color: #FFFFFF;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1A1D27;
        }

        /* Buttons */
        .stButton > button {
            background-color: #6C63FF;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 20px;
            font-size: 15px;
        }
        .stButton > button:hover {
            background-color: #5548e0;
        }

        /* Input boxes */
        .stTextInput > div > input {
            background-color: #1A1D27;
            color: white;
            border: 1px solid #6C63FF;
            border-radius: 8px;
        }

        /* Hide default streamlit menu */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)


# ─────────────────────────────────
# CREATE TABLES ON STARTUP
# ─────────────────────────────────

create_tables()


# ─────────────────────────────────
# SESSION STATE SETUP
# Session state = remembers things while app is running
# ─────────────────────────────────

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = ""

if "page" not in st.session_state:
    st.session_state.page = "login"   # start on login page


# ─────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────

def show_login():
    st.markdown("<h1 style='text-align:center; color:#6C63FF;'>📚 AI Study Platform</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray;'>Your personal AI-powered study assistant</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Center the form using columns
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 Login")
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        if st.button("Login", use_container_width=True):
            if username == "" or password == "":
                st.error("Please fill in all fields.")
            else:
                user = login_user(username, password)
                if user:
                    # Save user info to session
                    st.session_state.logged_in = True
                    st.session_state.user_id   = user["id"]
                    st.session_state.username  = user["username"]
                    st.session_state.page      = "dashboard"
                    st.rerun()
                else:
                    st.error("Wrong username or password.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("Don't have an account?")
        if st.button("Go to Register", use_container_width=True):
            st.session_state.page = "register"
            st.rerun()


# ─────────────────────────────────
# REGISTER PAGE
# ─────────────────────────────────

def show_register():
    st.markdown("<h1 style='text-align:center; color:#6C63FF;'>📚 Create Account</h1>", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("✏️ Register")
        username = st.text_input("Choose a Username", placeholder="e.g. john123")
        password = st.text_input("Choose a Password", type="password", placeholder="Min 6 characters")
        confirm  = st.text_input("Confirm Password",  type="password", placeholder="Repeat password")

        if st.button("Create Account", use_container_width=True):
            if username == "" or password == "":
                st.error("Please fill in all fields.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                success = register_user(username, password)
                if success:
                    st.success("Account created! Please login.")
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error("Username already taken. Try another.")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Back to Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()


# ─────────────────────────────────
# SIDEBAR  (shown after login)
# ─────────────────────────────────

def show_sidebar():
    with st.sidebar:
        st.markdown(f"### 👋 Hello, {st.session_state.username}!")
        st.markdown("---")

        # Navigation buttons
        pages = {
            "🏠 Dashboard":      "dashboard",
            "🤖 AI Tutor":       "ai_tutor",
            "📄 PDF Assistant":  "pdf_assistant",
            "📝 Quiz Generator": "quiz",
            "🃏 Flashcards":     "flashcards",
            "📅 Study Planner":  "planner",
            "📊 Analytics":      "analytics",
            "🔊 Audio Summary":  "audio",
            "🏆 Leaderboard":    "leaderboard",
            "⚙️ Settings":       "settings",
        }

        for label, page_name in pages.items():
            if st.button(label, use_container_width=True):
                st.session_state.page = page_name
                st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            # Clear session and go back to login
            st.session_state.logged_in = False
            st.session_state.user_id   = None
            st.session_state.username  = ""
            st.session_state.page      = "login"
            st.rerun()


# ─────────────────────────────────
# DASHBOARD PAGE (simple version)
# ─────────────────────────────────

def show_dashboard():
    from database import get_scores, get_average_score, get_flashcards

    st.title("🏠 Dashboard")
    st.markdown(f"Welcome back, **{st.session_state.username}**! Here's your study summary.")
    st.markdown("---")

    # Stats row
    scores    = get_scores(st.session_state.user_id)
    avg       = get_average_score(st.session_state.user_id)
    flashcards = get_flashcards(st.session_state.user_id)

    col1, col2, col3 = st.columns(3)
    col1.metric("📝 Quizzes Taken",   len(scores))
    col2.metric("⭐ Average Score",   f"{avg}%")
    col3.metric("🃏 Flashcards",      len(flashcards))

    st.markdown("---")

    # Recent quiz scores
    if scores:
        st.subheader("📊 Recent Quiz Scores")
        for s in scores[:5]:   # show last 5
            pct = round(s["score"] * 100 / s["total"], 1)
            st.write(f"**{s['subject']}** — {s['score']}/{s['total']} ({pct}%)  |  {s['created_at'][:10]}")
    else:
        st.info("No quizzes taken yet. Go to Quiz Generator to start!")


# ─────────────────────────────────
# PLACEHOLDER PAGES
# (we'll build each one separately)
# ─────────────────────────────────

def coming_soon(page_name):
    st.title(page_name)
    st.info("🚧 This page is coming soon! We'll build it next.")


# ─────────────────────────────────
# MAIN ROUTER
# Decides which page to show
# ─────────────────────────────────

def main():

    # If not logged in → show login or register
    if not st.session_state.logged_in:
        if st.session_state.page == "register":
            show_register()
        else:
            show_login()
        return   # stop here, don't show sidebar

    # If logged in → show sidebar + the selected page
    show_sidebar()

    page = st.session_state.page

    if   page == "dashboard":    show_dashboard()
    elif page == "ai_tutor":     show_ai_tutor()
    elif page == "pdf_assistant":show_pdf_assistant()
    elif page == "quiz":         coming_soon("📝 Quiz Generator")
    elif page == "flashcards":   coming_soon("🃏 Flashcards")
    elif page == "planner":      coming_soon("📅 Study Planner")
    elif page == "analytics":    coming_soon("📊 Analytics")
    elif page == "audio":        coming_soon("🔊 Audio Summary")
    elif page == "leaderboard":  coming_soon("🏆 Leaderboard")
    elif page == "settings":     coming_soon("⚙️ Settings")
    else:
        show_dashboard()


# Run the app
main()