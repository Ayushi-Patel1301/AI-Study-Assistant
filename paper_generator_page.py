import streamlit as st
from paper_generator_agent import PaperGeneratorAgent

def render_page():
    st.title("📝 Question Paper Generator")
    st.caption("Generate professional exam papers with Kenzo AI")
    st.divider()

    # ── Inputs ──────────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    title   = c1.text_input("Paper Title", placeholder="e.g. Mid-Term Examination 2025")
    subject = c2.text_input("Subject", placeholder="e.g. Data Structures")
    topics  = st.text_area("Topics / Chapters", placeholder="List topics, one per line", height=100)

    c3, c4, c5 = st.columns(3)
    total_marks = c3.number_input("Total Marks", min_value=5, max_value=500, value=100, step=5)
    difficulty  = c4.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)
    language    = c5.selectbox("Language", ["English", "Hindi", "Gujarati", "Marathi", "Tamil", "Telugu", "Bengali", "Urdu", "Punjabi", "Kannada"])

    # ── Pattern ─────────────────────────────────────────────────────────────
    st.subheader("Paper Pattern")
    mode = st.radio("", ["Auto Generate Pattern", "Custom Pattern"], horizontal=True, label_visibility="collapsed")

    custom_pattern = None
    if mode == "Custom Pattern":
        cols = st.columns(4)
        labels = ["MCQ", "Short Answer", "Medium Answer", "Long Answer"]
        keys   = ["mcq", "short", "medium", "long"]
        defaults_count = [10, 5, 4, 2]
        defaults_marks = [1,  2,  5, 10]
        custom_pattern = {}
        for col, lbl, key, dc, dm in zip(cols, labels, keys, defaults_count, defaults_marks):
            with col:
                st.markdown(f"**{lbl}**")
                custom_pattern[f"{key}_count"] = st.number_input("Questions", 0, 50, dc, key=f"{key}_c")
                custom_pattern[f"{key}_marks"] = st.number_input("Marks each", 0, 100, dm, key=f"{key}_m")
        computed = sum(custom_pattern[f"{k}_count"] * custom_pattern[f"{k}_marks"] for k in keys)
        color = "green" if computed == total_marks else "red"
        st.markdown(f"Pattern Total: :{color}[**{computed} / {int(total_marks)} marks**]")

    # ── Options ─────────────────────────────────────────────────────────────
    st.divider()
    instructions       = st.text_area("Additional Instructions (optional)",
                                      placeholder="e.g. Include numerical problems • Focus on Unit 3 • Add diagram questions",
                                      height=80)
    include_answer_key = st.checkbox("📘 Generate Answer Key")

    # ── Generate ─────────────────────────────────────────────────────────────
    st.divider()
    if st.button("📝 Generate Question Paper", type="primary", use_container_width=True):
        missing = [f for f, v in [("Paper Title", title), ("Subject", subject), ("Topics", topics)] if not v.strip()]
        if missing:
            st.error(f"Required fields missing: {', '.join(missing)}")
        else:
            with st.spinner("Kenzo AI is generating your paper…"):
                try:
                    st.session_state.generated_paper = PaperGeneratorAgent().generate_paper(
                        title, subject, topics, int(total_marks), difficulty,
                        custom_pattern, instructions, include_answer_key, language
                    )
                    st.session_state.paper_saved = False  # ANALYTICS: reset flag for new paper
                except Exception as e:
                    st.error(f"Generation failed: {e}")

    # ── Output ───────────────────────────────────────────────────────────────
    if st.session_state.get("generated_paper"):

        # ANALYTICS TRACKING: runs once per generated paper
        if not st.session_state.get("paper_saved", False):
            if "papers_generated" not in st.session_state:
                st.session_state.papers_generated = 0
            if "activity_history" not in st.session_state:
                st.session_state.activity_history = []
            st.session_state.papers_generated += 1
            st.session_state.activity_history.append(f"Generated paper: {subject if subject.strip() else 'Unknown'}")
            st.session_state.paper_saved = True  # ANALYTICS: mark as saved
        # END ANALYTICS TRACKING

        st.divider()
        st.subheader("📄 Generated Question Paper")
        st.markdown('<div style="background:white;border:1.5px solid #DBEAFE;border-radius:14px;padding:32px 40px;">', unsafe_allow_html=True)
        st.markdown(st.session_state.generated_paper)
        st.markdown('</div>', unsafe_allow_html=True)
        st.divider()
        c5, c6, _ = st.columns([1, 1, 3])
        if c5.button("🔄 Regenerate", use_container_width=True):
            if title.strip() and subject.strip() and topics.strip():
                with st.spinner("Regenerating…"):
                    try:
                        st.session_state.generated_paper = PaperGeneratorAgent().generate_paper(
                            title, subject, topics, int(total_marks), difficulty,
                            custom_pattern, instructions, include_answer_key, language
                        )
                        st.session_state.paper_saved = False  # ANALYTICS: reset so regenerate is also tracked
                        st.rerun()
                    except Exception as e:
                        st.error(f"Regeneration failed: {e}")
        c6.download_button("⬇️ Download", st.session_state.generated_paper,
                           file_name="question_paper.txt", use_container_width=True)

if __name__ == "__main__":
    st.set_page_config(page_title="Question Paper Generator – Kenzo AI", page_icon="📝", layout="wide")
    render_page()