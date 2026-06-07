# import streamlit as st
# import dashboard_page
# import tutor_page
# import pdf_page
# import quiz_page
# import flashcard_page
# import planner_page

# def show():

#     # ---------------- SYNC NAV ----------------
#     if "nav" not in st.session_state:
#         st.session_state.nav = "Home"

#     # Sidebar (still works)
#     menu = st.sidebar.radio(
#         "📚 KENZO AI",
#         ["Home", "AI Tutor", "PDF Q&A", "Quiz", "Flashcards", "Planner"],
#         index=0
#     )

#     # Sync sidebar → state
#     st.session_state.nav = menu

#     # Sync cards → sidebar
#     menu = st.session_state.nav

#     # ---------------- ROUTING ----------------
#     if menu == "Home":
#         dashboard_page.show()

#     elif menu == "AI Tutor":
#         tutor_page.show()

#     elif menu == "PDF Q&A":
#         pdf_page.show()

#     elif menu == "Quiz":
#         quiz_page.show()

#     elif menu == "Flashcards":
#         flashcard_page.show()

#     elif menu == "Planner":
#         planner_page.show()