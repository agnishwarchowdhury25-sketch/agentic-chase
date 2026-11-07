import streamlit as st
import pandas as pd
import plotly.express as px
import db, rag, agents
from chat_parser import parse

db.init()
st.set_page_config(page_title="Agentic Chase", layout="wide")
st.title("💬 Chat Intelligence Platform")

with st.sidebar:
    st.header("Upload")
    proj_in = st.text_input("Project name", "Suman")
    files = st.file_uploader("WhatsApp .txt exports", type="txt", accept_multiple_files=True)
    if st.button("Process") and files:
        for f in files:
            df = parse(f.read().decode("utf-8", errors="ignore"))
            if df.empty:
                st.error(f"{f.name}: couldn't parse")
                continue
            cid = db.save_chat(proj_in, f.name.replace(".txt", ""), df)
            rag.index_chat(cid, df)
        st.success("Done")
        st.rerun()

    chats = db.list_chats()
    if not chats:
        st.info("Upload a chat to begin")
        st.stop()
    project = st.selectbox("Project", sorted({c["project"] for c in chats}))
    pchats = [c for c in chats if c["project"] == project]
    st.caption("  \n".join(f"• {c['name']} ({c['type']})" for c in pchats))
    scope = st.selectbox("Scope", ["Whole project"] + [c["name"] for c in pchats])
    sel = pchats if scope == "Whole project" else [c for c in pchats if c["name"] == scope]
    sel_ids = [c["chat_id"] for c in sel]

df = pd.concat([db.messages(i) for i in sel_ids])
people = sorted(df.sender.unique())

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🤖 Agents", "⚙️ Privacy"])

with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Messages", len(df))
    c2.metric("Participants", len(people))
    c3.metric("Type", sel[0]["type"] if len(sel) == 1 else "mixed")
    top = df.sender.value_counts().reset_index()
    top.columns = ["sender", "count"]
    st.plotly_chart(px.bar(top, x="sender", y="count", title="Who talks most"), use_container_width=True)
    heat = df.assign(h=df.ts.dt.hour, d=df.ts.dt.day_name()).groupby(["d", "h"]).size().reset_index(name="n")
    st.plotly_chart(px.density_heatmap(heat, x="h", y="d", z="n", title="Activity by hour"), use_container_width=True)
    mon = df.groupby(df.ts.dt.to_period("M").astype(str)).size().reset_index(name="messages")
    mon.columns = ["month", "messages"]
    st.plotly_chart(px.line(mon, x="month", y="messages", title="Activity over time"), use_container_width=True)

with tab2:
    agent = st.radio("Agent", ["Deep Analyzer", "Roaster", "Reply Giver", "Memory Recall"], horizontal=True)
    cols = st.columns(3)
    person = cols[0].selectbox("Focus on participant", [None] + people)
    tone, optout = "Mild", []
    if agent == "Roaster":
        tone = cols[1].select_slider("Roast level", ["Mild", "Medium", "Spicy"])
        optout = cols[2].multiselect("Opted out (never roast)", people)

    key = f"hist_{agent}_{scope}"
    st.session_state.setdefault(key, [])
    for q, a, ev in st.session_state[key]:
        st.chat_message("user").write(q)
        with st.chat_message("assistant"):
            st.write(a)
            if ev:
                with st.expander(f"🧾 Evidence ({len(ev)})"):
                    for e in ev:
                        st.markdown(e)
            else:
                st.caption("No direct chat evidence found.")
    hint = {"Reply Giver": "Paste the message you need to reply to...", "Roaster": "Who to roast and why?"}.get(agent, "Ask anything about this chat...")
    if q := st.chat_input(hint):
        with st.spinner("Thinking..."):
            try:
                a, ev = agents.run_agent(agent, sel_ids, q, person, tone, optout)
            except Exception as e:
                a, ev = f"⚠️ {e}", []
        st.session_state[key].append((q, a, ev))
        st.rerun()

with tab3:
    st.write("Each chat has its own isolated memory. Delete removes messages and vector memory.")
    for c in pchats:
        if st.button(f"🗑 Delete '{c['name']}'", key=c["chat_id"]):
            db.delete_chat(c["chat_id"])
            rag.delete_index(c["chat_id"])
            st.rerun()