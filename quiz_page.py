# import streamlit as st
# from quiz_agent import generate_quiz
# def show():
#     st.title("🧠 Quiz Generator")
#     topic = st.text_input("Enter Topic")
#     num_questions = st.number_input(
#         "Number of Questions",
#         min_value=1,
#         max_value=20,
#         value=5
#     )
#     difficulty = st.selectbox(
#         "Difficulty",
#         ["Easy", "Medium", "Hard"]
#     )
#     language = st.selectbox(
#         "🌐 Language",
#         [
#             "English",
#             "Hindi",
#             "Gujarati",
#             "Spanish",
#             "French",
#             "German",
#             "Arabic",
#             "Chinese (Simplified)",
#             "Japanese",
#             "Portuguese",
#         ]
#     )
#     if st.button("Generate Quiz"):
#         with st.spinner("Generating Quiz..."):
#             quiz = generate_quiz(topic, num_questions, difficulty, language)
#             st.session_state.quiz = quiz
#             st.session_state.submitted = False
#             for key in list(st.session_state.keys()):
#                 if key.startswith("q_"):
#                     del st.session_state[key]
#     if "quiz" in st.session_state and st.session_state.quiz:
#         st.markdown("---")
#         for i, q in enumerate(st.session_state.quiz):
#             st.subheader(f"Q{i+1}. {q['question']}")
#             answer = st.radio(
#                 "Choose an option:",
#                 q["options"],
#                 key=f"q_{i}",
#                 index=None
#             )
#             if st.session_state.get("submitted"):
#                 selected = st.session_state.get(f"q_{i}")
#                 correct = q["answer"]
#                 if selected is None:
#                     st.warning(f"⚠️ You didn't answer this question. Correct answer: **{correct}**")
#                 elif selected == correct:
#                     st.success(f"✅ Correct! **{correct}**")
#                 else:
#                     st.error(f"❌ Wrong! You chose: **{selected}**")
#                     st.info(f"💡 Correct answer: **{correct}**")
#             st.markdown("")
#         if not st.session_state.get("submitted"):
#             if st.button("Submit Quiz"):
#                 st.session_state.submitted = True
#                 st.rerun()
#         if st.session_state.get("submitted"):
#             score = sum(
#                 1 for i, q in enumerate(st.session_state.quiz)
#                 if st.session_state.get(f"q_{i}") == q["answer"]
#             )
#             total = len(st.session_state.quiz)
#             percentage = round((score / total) * 100, 2)
#             st.markdown("---")
#             st.success(f"🎯 Score: {score}/{total}")
#             st.info(f"📊 Percentage: {percentage}%")
#             if st.button("🔄 Retake / New Quiz"):
#                 st.session_state.submitted = False
#                 del st.session_state.quiz
#                 for key in list(st.session_state.keys()):
#                     if key.startswith("q_"):
#                         del st.session_state[key]
#                 st.rerun()

import streamlit as st
from quiz_agent import generate_quiz

def show():
    st.title("🧠 Quiz Generator")
    topic = st.text_input("Enter Topic")
    num_questions = st.number_input(
        "Number of Questions",
        min_value=1,
        max_value=20,
        value=5
    )
    difficulty = st.selectbox(
        "Difficulty",
        ["Easy", "Medium", "Hard"]
    )
    language = st.selectbox(
        "🌐 Language",
        [
            "English",
            "Hindi",
            "Gujarati",
            "Spanish",
            "French",
            "German",
            "Arabic",
            "Chinese (Simplified)",
            "Japanese",
            "Portuguese",
        ]
    )
    if st.button("Generate Quiz"):
        with st.spinner("Generating Quiz..."):
            quiz = generate_quiz(topic, num_questions, difficulty, language)
            st.session_state.quiz = quiz
            st.session_state.submitted = False
            st.session_state.quiz_topic = topic  # ANALYTICS: store topic for activity log
            st.session_state.quiz_saved = False   # ANALYTICS: reset save flag for new quiz
            for key in list(st.session_state.keys()):
                if key.startswith("q_"):
                    del st.session_state[key]

    if "quiz" in st.session_state and st.session_state.quiz:
        st.markdown("---")
        for i, q in enumerate(st.session_state.quiz):
            st.subheader(f"Q{i+1}. {q['question']}")
            answer = st.radio(
                "Choose an option:",
                q["options"],
                key=f"q_{i}",
                index=None
            )
            if st.session_state.get("submitted"):
                selected = st.session_state.get(f"q_{i}")
                correct = q["answer"]
                if selected is None:
                    st.warning(f"⚠️ You didn't answer this question. Correct answer: **{correct}**")
                elif selected == correct:
                    st.success(f"✅ Correct! **{correct}**")
                else:
                    st.error(f"❌ Wrong! You chose: **{selected}**")
                    st.info(f"💡 Correct answer: **{correct}**")
            st.markdown("")

        if not st.session_state.get("submitted"):
            if st.button("Submit Quiz"):
                st.session_state.submitted = True
                st.session_state.quiz_saved = False  # ANALYTICS: allow saving on new submit
                st.rerun()

        if st.session_state.get("submitted"):
            score = sum(
                1 for i, q in enumerate(st.session_state.quiz)
                if st.session_state.get(f"q_{i}") == q["answer"]
            )
            total = len(st.session_state.quiz)
            percentage = round((score / total) * 100, 2)

            # ── ANALYTICS TRACKING ────────────────────────────────────────
            # Only save once per submission to prevent duplicate on rerun
            if not st.session_state.get("quiz_saved", False):
                # Init session state variables if not present
                if "quiz_count" not in st.session_state:
                    st.session_state.quiz_count = 0
                if "quiz_scores" not in st.session_state:
                    st.session_state.quiz_scores = []
                if "activity_history" not in st.session_state:
                    st.session_state.activity_history = []

                # Save quiz data
                st.session_state.quiz_count += 1
                st.session_state.quiz_scores.append(percentage)
                topic_label = st.session_state.get("quiz_topic", "Unknown")
                st.session_state.activity_history.append(
                    f"Completed quiz on {topic_label} ({percentage}%)"
                )
                st.session_state.quiz_saved = True  # mark as saved
            # ── END ANALYTICS TRACKING ────────────────────────────────────

            st.markdown("---")
            st.success(f"🎯 Score: {score}/{total}")
            st.info(f"📊 Percentage: {percentage}%")

            if st.button("🔄 Retake / New Quiz"):
                st.session_state.submitted = False
                del st.session_state.quiz
                for key in list(st.session_state.keys()):
                    if key.startswith("q_"):
                        del st.session_state[key]
                st.rerun()