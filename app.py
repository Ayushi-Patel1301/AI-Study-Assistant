import streamlit as st
import dashboard_page
import tutor_page
import pdf_page
import quiz_page
import paper_generator_page
import planner_page
import Analytics_page

st.set_page_config(page_title="KENZO AI", layout="wide")

if "nav" not in st.session_state:
    st.session_state.nav = "Home"


def back_button():
    if st.button("⬅ Back to Home"):
        st.session_state.nav = "Home"


page = st.session_state.nav

if page == "Home":
    dashboard_page.show()

elif page == "AI Tutor":
    back_button()
    tutor_page.show()

elif page == "PDF Q&A":
    back_button()
    pdf_page.show()

elif page == "Quiz":
    back_button()
    quiz_page.show()

elif page == "Question Paper":
    back_button()
    paper_generator_page.render_page()

elif page == "Planner":
    back_button()
    planner_page.show()

elif page == "Analytics":
    back_button()
    Analytics_page.show()