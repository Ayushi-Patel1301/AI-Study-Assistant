import streamlit as st


def show():
    st.title("📊 Analytics")
    st.caption("Track your learning progress and activity.")
    st.divider()

    # ── Defaults ──────────────────────────────────────────────────────────
    ai_q     = st.session_state.get("ai_questions", 0)
    quiz_c   = st.session_state.get("quiz_count", 0)
    pdf_c    = st.session_state.get("pdf_count", 0)
    tasks_c  = sum(1 for t in st.session_state.get("tasks", []) if t["completed"])
    papers_c = st.session_state.get("papers_generated", 0)
    scores   = st.session_state.get("quiz_scores", [])
    activity = st.session_state.get("activity_history", [])

    # ── Overview ──────────────────────────────────────────────────────────
    st.subheader("📈 Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🤖 AI Tutor Questions", ai_q)
    c2.metric("🧠 Quizzes Attempted",  quiz_c)
    c3.metric("📄 PDFs Uploaded",      pdf_c)
    c4.metric("📋 Tasks Completed",    tasks_c)

    st.divider()

    # ── Quiz Performance ──────────────────────────────────────────────────
    st.subheader("🧠 Quiz Performance")
    avg_score  = round(sum(scores) / len(scores), 1) if scores else 0
    best_score = max(scores) if scores else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("📊 Average Score", avg_score)
    c2.metric("🏆 Best Score",    best_score)
    c3.metric("📝 Total Quizzes", len(scores) or quiz_c)

    st.divider()

    # ── Learning Progress ─────────────────────────────────────────────────
    st.subheader("📚 Learning Progress")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🤖 AI Questions",     ai_q)
    c2.metric("🧠 Quiz Attempts",    quiz_c)
    c3.metric("📄 PDF Uploads",      pdf_c)
    c4.metric("📋 Papers Generated", papers_c)
    c5.metric("✅ Tasks Done",       tasks_c)

    st.divider()

    # ── Recent Activity ───────────────────────────────────────────────────
    st.subheader("🕒 Recent Activity")
    if not activity:
        st.info("No activity yet.")
    else:
        for item in reversed(activity[-10:]):
            st.write(f"• {item}")

    st.divider()

    # ── Highlights ────────────────────────────────────────────────────────
    st.subheader("🏆 Highlights")
    feature_map = {"AI Tutor": ai_q, "Quiz": quiz_c, "PDF": pdf_c, "Planner": tasks_c, "Papers": papers_c}
    most_used = max(feature_map, key=feature_map.get) if any(feature_map.values()) else "N/A"
    c1, c2, c3 = st.columns(3)
    c1.metric("🏆 Best Quiz Score",   best_score)
    c2.metric("🏆 Most Used Feature", most_used)
    c3.metric("🏆 Total Activities",  len(activity))