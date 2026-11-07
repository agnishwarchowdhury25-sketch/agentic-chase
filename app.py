import streamlit as st
import pandas as pd
import plotly.express as px
import db, rag, agents, style
from chat_parser import parse

try:
    import memory_tab
except Exception:
    memory_tab = None

db.init()
st.set_page_config(page_title="Agentic Chase", page_icon="💬", layout="wide")
style.inject()
style.hero()

AGENTS = {
    "Deep Analyzer": ("🔍", "Finds patterns, moods and who drives the chat"),
    "Roaster": ("🔥", "Playful roasts built from real chat habits"),
    "Reply Giver": ("💬", "Gives 3 reply options in someone's style"),
    "Memory Recall": ("🧠", "Finds plans, promises and past events"),
}
EXAMPLES = {
    "Deep Analyzer": ["Who starts the most conversations?", "How did the mood change over time?", "Who is the funniest person here?"],
    "Roaster": ["Roast the biggest voice-note sender", "Roast the person who replies slowest", "Roast the group's favourite slang"],
    "Reply Giver": ["Documentation kaun likhega?", "Are you coming tomorrow?", "Did you finish your part?"],
    "Memory Recall": ["What deadlines were mentioned?", "Who promised to do what?", "What did we plan for the demo?"],
}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
BADGE = "✅ Passed safety check"
CFG = {"displayModeBar": False}

if "flash" in st.session_state:
    st.toast(st.session_state.pop("flash"), icon="✅")

with st.sidebar:
    st.markdown("### 📤 1 · Upload")
    proj_in = st.text_input("Project name", "Suman")
    files = st.file_uploader("WhatsApp .txt exports", type="txt", accept_multiple_files=True)
    if st.button("⚡ Process chats", use_container_width=True) and files:
        existing = {(c["project"], c["name"]) for c in db.list_chats()}
        added = 0
        for f in files:
            name = f.name.replace(".txt", "")
            if (proj_in, name) in existing:
                st.warning(f"'{f.name}' is already in project '{proj_in}', skipped")
                continue
            parsed = parse(f.read().decode("utf-8", errors="ignore"))
            if parsed.empty:
                st.error(f"{f.name}: couldn't parse")
                continue
            cid = db.save_chat(proj_in, name, parsed)
            rag.index_chat(cid, parsed)
            added += 1
        if added:
            st.session_state["flash"] = f"Added {added} chat(s)"
            st.rerun()

    chats = db.list_chats()
    if chats:
        st.divider()
        st.markdown("### 🎯 2 · Choose")
        project = st.selectbox("Project", sorted({c["project"] for c in chats}))
        pchats = [c for c in chats if c["project"] == project]
        st.caption("  \n".join(f"{'👥' if c['type'] == 'group' else '👤'} {c['name']} ({c['type']})" for c in pchats))
        scope = st.selectbox("Scope", ["Whole project"] + [c["name"] for c in pchats])
        sel = pchats if scope == "Whole project" else [c for c in pchats if c["name"] == scope]
        sel_ids = [c["chat_id"] for c in sel]

if not chats:
    st.info("👈 Upload a WhatsApp .txt export in the sidebar and click **Process chats** to begin.")
    st.stop()

df = pd.concat([db.messages(i) for i in sel_ids])
people = sorted(df.sender.unique())

style.chips([f"📁 {project}", f"💬 {len(df)} messages", f"👥 {len(people)} people", f"🗂️ {len(sel)} chat(s)"])


def show(answer, ev):
    safe = BADGE in answer
    st.markdown(answer.replace(BADGE, "").strip())
    if safe:
        style.badge()
    if ev:
        with st.expander(f"🧾 Evidence ({len(ev)})"):
            for e in ev:
                st.markdown(e)


labels = ["📊 Dashboard", "🤖 Agents", "⚙️ Privacy"]
if memory_tab:
    labels.insert(2, "🧠 Memory")
tabs = st.tabs(labels)
tab_dash, tab_agents, tab_priv = tabs[0], tabs[1], tabs[-1]
tab_mem = tabs[2] if memory_tab else None

with tab_dash:
    c1, c2, c3 = st.columns(3)
    c1.metric("Messages", len(df))
    c2.metric("Participants", len(people))
    c3.metric("Type", sel[0]["type"] if len(sel) == 1 else "mixed")

    style.section("Chat Wrapped", "your chat in six cards")
    cards = style.wrapped(df)
    for start in (0, 3):
        for col, (i, card) in zip(st.columns(3), enumerate(cards[start:start + 3], start)):
            col.markdown(style.card(*card, i=i), unsafe_allow_html=True)

    style.section("Activity", "who talks and when")
    left, right = st.columns(2)
    top = df.sender.value_counts().reset_index()
    top.columns = ["sender", "messages"]
    fig1 = px.bar(top, x="sender", y="messages", color="sender",
                  color_discrete_sequence=style.COLORS, title="Who talks most")
    with left.container(border=True):
        st.plotly_chart(style.pretty(fig1), width="stretch", config=CFG)

    heat = df.assign(h=df.ts.dt.hour, d=df.ts.dt.day_name()).groupby(["d", "h"]).size().reset_index(name="n")
    fig2 = px.density_heatmap(heat, x="h", y="d", z="n", category_orders={"d": DAYS},
                              color_continuous_scale=["#1b1f2e", "#7C5CFF", "#FF6AD5"],
                              title="Activity by hour")
    with right.container(border=True):
        st.plotly_chart(style.pretty(fig2), width="stretch", config=CFG)

    mon = df.groupby(df.ts.dt.to_period("M").astype(str)).size().reset_index(name="messages")
    mon.columns = ["month", "messages"]
    fig3 = px.line(mon, x="month", y="messages", markers=True, title="Activity over time",
                   color_discrete_sequence=[style.COLORS[1]])
    with st.container(border=True):
        st.plotly_chart(style.pretty(fig3), width="stretch", config=CFG)

with tab_agents:
    style.section("Talk to an agent", "answers come with real messages as proof")
    agent = st.radio("Choose an agent", list(AGENTS), horizontal=True,
                     format_func=lambda a: f"{AGENTS[a][0]} {a}", label_visibility="collapsed")
    icon = AGENTS[agent][0]
    st.caption(f"{icon} {AGENTS[agent][1]}")

    cols = st.columns(3)
    person = cols[0].selectbox("Focus on participant", [None] + people)
    tone, optout = "Mild", []
    if agent == "Roaster":
        tone = cols[1].select_slider("Roast level", ["Mild", "Medium", "Spicy"])
        optout = cols[2].multiselect("Opted out (never roast)", people)

    key = f"hist_{agent}_{scope}"
    st.session_state.setdefault(key, [])

    if st.session_state[key]:
        if st.button("🧹 New conversation"):
            st.session_state[key] = []
            st.rerun()
    else:
        st.markdown("**Try one of these:**")
        for col, ex in zip(st.columns(3), EXAMPLES[agent]):
            if col.button(ex, key=f"ex_{agent}_{ex}", use_container_width=True):
                st.session_state["pending_q"] = ex
                st.rerun()

    for q, a, ev in st.session_state[key]:
        st.chat_message("user", avatar="🧑").write(q)
        with st.chat_message("assistant", avatar=icon):
            show(a, ev)

    hint = {"Reply Giver": "Paste the message you need to reply to...",
            "Roaster": "Who to roast and why?"}.get(agent, "Ask anything about this chat...")
    typed = st.chat_input(hint)
    q = typed or st.session_state.pop("pending_q", None)
    if q:
        hist = [(x[0], x[1]) for x in st.session_state[key]]
        st.chat_message("user", avatar="🧑").write(q)
        with st.chat_message("assistant", avatar=icon):
            ev = []
            try:
                if hasattr(agents, "chat_stream"):
                    res = {}
                    text = st.write_stream(agents.chat_stream(agent, sel_ids, q, person, tone, optout, hist, res))
                    answer = res.get("answer", text)
                    ev = res.get("evidence", [])
                else:
                    with st.spinner("Thinking..."):
                        answer, ev = agents.run_agent(agent, sel_ids, q, person, tone, optout)
                    st.markdown(answer)
            except Exception as e:
                answer = f"⚠️ {e}"
                st.error(answer)
        st.session_state[key].append((q, answer, ev))
        st.rerun()

if tab_mem is not None:
    with tab_mem:
        memory_tab.render(sel)

with tab_priv:
    style.section("Privacy and control", "your chats stay yours")
    st.markdown(
        "- 🔒 Each chat has its own **isolated** memory\n"
        "- 🗑 Deleting a chat removes its **messages and search memory**\n"
        "- 🔑 API keys stay in `.env` and are **never uploaded**"
    )
    for c in pchats:
        n = len(db.messages(c["chat_id"]))
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.markdown(f"**{c['name']}** · {c['type']} · {n} messages")
            if right.button("🗑 Delete", key=c["chat_id"], use_container_width=True):
                db.delete_chat(c["chat_id"])
                rag.delete_index(c["chat_id"])
                st.rerun()