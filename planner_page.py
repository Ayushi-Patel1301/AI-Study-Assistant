# import streamlit as st

# def show():

#     st.title("📅 Study Planner")

#     task = st.text_input("Task title")
#     date = st.date_input("Due date")

#     if st.button("Add Task"):
#         st.success("Task added successfully")


import streamlit as st
from datetime import date

def show():
    st.title("📅 Task Manager")
    st.caption("Manage tasks, deadlines, and study goals in one place.")
    st.divider()

    if "tasks" not in st.session_state:
        st.session_state.tasks = []

    # ── Add Task ─────────────────────────────────────────────────────────
    st.subheader("➕ Add Task")
    c1, c2 = st.columns(2)
    task_name = c1.text_input("Task Name", placeholder="e.g. Read Chapter 5")
    subject   = c2.text_input("Subject", placeholder="e.g. Physics")
    c3, c4 = st.columns(2)
    due_date = c3.date_input("Due Date", min_value=date.today())
    priority = c4.radio("Priority", ["Low", "Medium", "High"], horizontal=True)

    if st.button("➕ Add Task", type="primary"):
        if task_name.strip() and subject.strip():
            st.session_state.tasks.append({
                "name": task_name.strip(),
                "subject": subject.strip(),
                "due_date": due_date,
                "priority": priority,
                "completed": False,
            })
            st.success(f"Task '{task_name}' added!")
            st.rerun()
        else:
            st.error("Please enter Task Name and Subject.")

    st.divider()

    # ── Task List ─────────────────────────────────────────────────────────
    st.subheader("📋 Task List")
    if not st.session_state.tasks:
        st.info("No tasks yet. Add a task above.")
    else:
        priority_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
        for i, task in enumerate(st.session_state.tasks):
            c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 2, 1.5, 1.2, 1])
            c1.markdown(f"{'~~' if task['completed'] else ''}**{task['name']}**{'~~' if task['completed'] else ''}")
            c2.markdown(task["subject"])
            c3.markdown(str(task["due_date"]))
            c4.markdown(f"{priority_color[task['priority']]} {task['priority']}")
            done = c5.checkbox("Done", value=task["completed"], key=f"done_{i}")
            if done != task["completed"]:
                st.session_state.tasks[i]["completed"] = done
                st.rerun()
            if c6.button("🗑", key=f"del_{i}"):
                st.session_state.tasks.pop(i)
                st.rerun()

    st.divider()

    # ── Overview ──────────────────────────────────────────────────────────
    st.subheader("📊 Overview")
    total     = len(st.session_state.tasks)
    completed = sum(1 for t in st.session_state.tasks if t["completed"])
    pending   = total - completed
    rate      = f"{int(completed / total * 100)}%" if total else "0%"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋 Total Tasks", total)
    c2.metric("✅ Completed",   completed)
    c3.metric("⏳ Pending",     pending)
    c4.metric("📈 Completion",  rate)