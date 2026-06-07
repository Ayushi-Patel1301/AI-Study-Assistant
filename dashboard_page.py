import streamlit as st
import streamlit.components.v1 as components


def go(page):
    st.session_state.nav = page


def title():
    st.markdown("""
    <div style="text-align:center;">
        <span style="font-size:72px; font-weight:900; color:#2563EB;">KENZO</span>
        <span style="font-size:74px; font-weight:900; color:#111827;">AI</span>
        <p style="color:#475569; font-size:17px;">Your Personal AI Study Assistant</p>
    </div>
    """, unsafe_allow_html=True)


def stats():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📄 PDFs", 0)
    c2.metric("🧠 Quizzes", 0)
    c3.metric("📝 Papers", 0)
    c4.metric("🔥 Streak", "1 Day")


def card_grid():
    # nav_key must exactly match the elif branch in app.py
    cards = [
        ("🤖", "AI Tutor",                "Instant explanations for any topic",   "AI Tutor"),
        ("📄", "PDF Assistant",                 "Get Answer from uploaded PDFs",     "PDF Q&A"),
        ("🧠", "Quiz Generator",           "Auto MCQs from any topic",             "Quiz"),
        ("📝", "Question Paper Generator", "Generate professional exam papers",    "Question Paper"),
        ("📅", "Task Manager",            "Plan your daily study schedule",       "Planner"),
        ("📊", "Analytics", "Track your learning progress", "Analytics"),
    ]

    # Hidden Streamlit buttons — key = nav_key for reliable matching
    st.markdown('<style>.hidden-btn-row{display:none!important;}</style>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="hidden-btn-row">', unsafe_allow_html=True)
        cols = st.columns(len(cards))
        clicked = {}
        for i, (icon, name, desc, nav_key) in enumerate(cards):
            with cols[i]:
                clicked[nav_key] = st.button(nav_key, key=f"nav_{nav_key}")
        st.markdown('</div>', unsafe_allow_html=True)

    # HTML card grid — JS clicks the hidden button by matching nav_key text
    cards_html = "".join(f"""
        <div class="card" onclick="triggerNav('{nav_key}')">
            <div class="card-icon">{icon}</div>
            <div class="card-title">{name}</div>
            <div class="card-desc">{desc}</div>
        </div>""" for icon, name, desc, nav_key in cards)

    components.html(f"""
    <style>
        *{{box-sizing:border-box;margin:0;padding:0;}}
        body{{background:transparent;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
        .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;padding:4px;}}
        .card{{background:white;border-radius:20px;border:1.5px solid #DBEAFE;padding:26px;
               height:220px;display:flex;flex-direction:column;justify-content:center;
               box-shadow:0 6px 18px rgba(37,99,235,0.10);
               transition:transform .2s,box-shadow .2s,border-color .2s;cursor:pointer;user-select:none;}}
        .card:hover{{transform:translateY(-5px);border-color:#93C5FD;box-shadow:0 12px 28px rgba(37,99,235,0.18);}}
        .card:active{{transform:translateY(-2px);}}
        .card-icon{{font-size:32px;margin-bottom:10px;}}
        .card-title{{font-size:20px;font-weight:800;color:#0F172A;}}
        .card-desc{{font-size:14px;color:#64748B;margin-top:8px;}}
    </style>
    <div class="grid">{cards_html}</div>
    <script>
    function triggerNav(navKey) {{
        var buttons = window.parent.document.querySelectorAll('button');
        for (var i = 0; i < buttons.length; i++) {{
            if (buttons[i].innerText.trim() === navKey) {{
                buttons[i].click();
                return;
            }}
        }}
    }}
    </script>
    """, height=500, scrolling=False)

    # Handle clicks
    for icon, name, desc, nav_key in cards:
        if clicked[nav_key]:
            st.session_state.nav = nav_key
            st.rerun()


def show():
    st.markdown('<style>[data-testid="stAppViewContainer"]{background:#EFF6FF;}</style>', unsafe_allow_html=True)
    title()
    st.markdown("---")
    stats()
    st.markdown("---")
    card_grid()


def stats():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📄 PDFs",    st.session_state.get("pdf_count", 0))
    c2.metric("🧠 Quizzes", st.session_state.get("quiz_count", 0))
    c3.metric("📝 Papers",  st.session_state.get("papers_generated", 0))
    c4.metric("✅ Tasks",   sum(1 for t in st.session_state.get("tasks", []) if t["completed"]))