import streamlit as st
from pdf_agent import PDFAgent

agent = PDFAgent()

def show():
    st.title("📄 PDF Assistant")
    st.caption("Upload your notes, textbooks, assignments, or PYQ papers and ask questions.")
    st.divider()

    # ── Upload ───────────────────────────────────────────────────────────
    pdf_file = st.file_uploader("Upload a PDF", type="pdf")

    if pdf_file:
        if "pdf_text" not in st.session_state or st.session_state.get("pdf_name") != pdf_file.name:
            with st.spinner("Reading PDF…"):
                st.session_state.pdf_text = agent.extract_text(pdf_file)
                st.session_state.pdf_name = pdf_file.name
                st.session_state.chat_history = []
                st.session_state.quiz = None
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
        st.success(f"✅ PDF uploaded successfully — {pdf_file.name}")

    if not st.session_state.get("pdf_text"):
        st.info("Please upload a PDF to get started.")
        return

    pdf_text = st.session_state.pdf_text

    # ── Quick Actions ─────────────────────────────────────────────────────
    st.subheader("Quick Actions")
    c1, c2, c3 = st.columns(3)

    if c1.button("📖 Summarize PDF", use_container_width=True):
        with st.spinner("Summarizing…"):
            result = agent.ask_pdf(pdf_text, "Summarize the entire PDF content clearly and concisely for a student.")
        st.session_state.chat_history.append(("You", "📖 Summarize PDF"))
        st.session_state.chat_history.append(("AI", result))

    if c2.button("🧠 Generate Quiz", use_container_width=True):
        with st.spinner("Generating quiz…"):
            try:
                st.session_state.quiz = agent.generate_quiz(pdf_text)
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
            except Exception as e:
                st.error(f"Quiz generation failed: {e}")

    if c3.button("⭐ Important Topics", use_container_width=True):
        with st.spinner("Finding key topics…"):
            result = agent.ask_pdf(pdf_text, "List the most important topics and key points from this PDF.")
        st.session_state.chat_history.append(("You", "⭐ Important Topics"))
        st.session_state.chat_history.append(("AI", result))

    # ── Interactive Quiz ──────────────────────────────────────────────────
    if st.session_state.get("quiz"):
        st.divider()
        st.subheader("🧠 Quiz")
        quiz = st.session_state.quiz
        submitted = st.session_state.get("quiz_submitted", False)

        for i, q in enumerate(quiz):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            options = q["options"]

            if submitted:
                selected = st.session_state.quiz_answers.get(i)
                correct = q["answer"]
                for opt in options:
                    if opt == correct:
                        st.markdown(f"✅ {opt}")
                    elif opt == selected and selected != correct:
                        st.markdown(f"❌ {opt}")
                    else:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{opt}")
                st.caption(f"💡 {q['explanation']}")
            else:
                choice = st.radio("", options, key=f"q{i}", index=None, label_visibility="collapsed")
                st.session_state.quiz_answers[i] = choice

            st.markdown("")

        if not submitted:
            if st.button("✅ Submit Quiz", type="primary"):
                st.session_state.quiz_submitted = True
                st.rerun()
        else:
            score = sum(1 for i, q in enumerate(quiz) if st.session_state.quiz_answers.get(i) == q["answer"])
            st.success(f"🎯 Your Score: {score} / {len(quiz)}")
            if st.button("🔄 Retake Quiz"):
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.rerun()

    st.divider()

    # ── Chat ──────────────────────────────────────────────────────────────
    st.subheader("Ask a Question")
    question = st.text_input("Ask anything about this PDF…", key="pdf_question")
    if st.button("Send", type="primary") and question.strip():
        with st.spinner("Thinking…"):
            answer = agent.ask_pdf(pdf_text, question)
        st.session_state.chat_history.append(("You", question))
        st.session_state.chat_history.append(("AI", answer))

    # ── Chat History ──────────────────────────────────────────────────────
    if st.session_state.get("chat_history"):
        st.divider()
        for role, msg in st.session_state.chat_history:
            st.markdown(f"**{'👤 You' if role == 'You' else '🤖 AI'}:** {msg}")
            st.markdown("")