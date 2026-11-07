import html
import streamlit as st
import pandas as pd

COLORS = ["#7C5CFF", "#FF6AD5", "#22D3EE", "#FBBF24", "#34D399", "#F87171"]

CSS = """
<style>
@keyframes fadeUp {from {opacity: 0; transform: translateY(14px);} to {opacity: 1; transform: none;}}
@keyframes shift {0% {background-position: 0% 50%;} 50% {background-position: 100% 50%;} 100% {background-position: 0% 50%;}}
@keyframes pulse {0%, 100% {box-shadow: 0 0 0 0 rgba(52,211,153,.55);} 50% {box-shadow: 0 0 0 8px rgba(52,211,153,0);}}
@keyframes float {0%, 100% {transform: translateY(0);} 50% {transform: translateY(-5px);}}

.block-container {padding-top: 1.6rem; max-width: 1180px;}
footer {visibility: hidden;}
[data-testid="stAppDeployButton"], .stDeployButton {display: none;}

.hero {padding: 1.5rem 1.8rem; border-radius: 22px; margin-bottom: 1rem;
  background: linear-gradient(120deg, rgba(124,92,255,.45), rgba(255,106,213,.25), rgba(34,211,238,.2), rgba(124,92,255,.45));
  background-size: 300% 300%; animation: shift 12s ease infinite, fadeUp .6s ease both;
  border: 1px solid rgba(255,255,255,.1);}
.hero-row {display: flex; align-items: center; gap: 1rem;}
.logo {font-size: 2.6rem; animation: float 3.5s ease-in-out infinite;}
.hero h1 {margin: 0; padding: 0; font-size: 2.1rem; font-weight: 800;
  background: linear-gradient(90deg, #ffffff, #d8ccff 55%, #ffb3ec);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
.hero p {margin: .25rem 0 0; opacity: .85;}
.live {display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: #34D399;
  margin-right: .45rem; animation: pulse 1.8s infinite;}
.livetxt {font-size: .8rem; opacity: .8; margin-top: .5rem;}

.chip {display: inline-block; padding: .28rem .75rem; margin: .2rem .4rem .6rem 0; border-radius: 999px;
  background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.12); font-size: .85rem;
  animation: fadeUp .5s ease both; transition: all .2s;}
.chip:hover {background: rgba(124,92,255,.25); border-color: #7C5CFF; transform: translateY(-2px);}

.sec {display: flex; align-items: center; gap: .6rem; margin: 1.2rem 0 .6rem;}
.sec .bar {width: 5px; height: 26px; border-radius: 4px; background: linear-gradient(180deg, #7C5CFF, #FF6AD5);}
.sec .tt {font-size: 1.25rem; font-weight: 700;}
.sec .ss {font-size: .85rem; opacity: .65; margin-left: .3rem;}

.wcard {padding: 1rem 1.1rem; border-radius: 18px; margin-bottom: .8rem; position: relative; overflow: hidden;
  background: linear-gradient(160deg, rgba(255,255,255,.06), rgba(22,27,38,.92));
  border: 1px solid rgba(255,255,255,.08); border-top: 3px solid var(--a, #7C5CFF);
  animation: fadeUp .6s ease both; transition: transform .2s, box-shadow .2s;}
.wcard:hover {transform: translateY(-5px) scale(1.015); box-shadow: 0 12px 30px rgba(0,0,0,.45), 0 0 22px var(--a, #7C5CFF);}
.wcard .e {font-size: 1.7rem;}
.wcard .t {font-size: .72rem; text-transform: uppercase; letter-spacing: .09em; opacity: .65; margin-top: .25rem;}
.wcard .v {font-size: 1.4rem; font-weight: 800; margin-top: .1rem;}
.wcard .s {font-size: .85rem; opacity: .7;}

div[data-testid="stMetric"] {background: rgba(255,255,255,.045); border: 1px solid rgba(255,255,255,.09);
  padding: .8rem 1rem; border-radius: 16px; animation: fadeUp .5s ease both; transition: all .2s;}
div[data-testid="stMetric"]:hover {border-color: #7C5CFF; transform: translateY(-3px);}

[data-testid="stSidebar"] {background: linear-gradient(180deg, #151a2b, #0E1117);
  border-right: 1px solid rgba(255,255,255,.06);}

.stTabs [data-baseweb="tab-list"] {gap: 6px; background: rgba(255,255,255,.04); padding: 6px; border-radius: 16px;}
.stTabs [data-baseweb="tab"] {border-radius: 12px; padding: .5rem 1.1rem; transition: all .2s;}
.stTabs [data-baseweb="tab"]:hover {background: rgba(124,92,255,.18);}
.stTabs [aria-selected="true"] {background: linear-gradient(90deg, #7C5CFF, #FF6AD5); color: white !important;}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {display: none;}

div[role="radiogroup"] > label {background: rgba(255,255,255,.045); border: 1px solid rgba(255,255,255,.1);
  padding: .4rem 1rem; border-radius: 999px; transition: all .2s; margin-right: .3rem;}
div[role="radiogroup"] > label:hover {border-color: #7C5CFF; transform: translateY(-2px);}
div[role="radiogroup"] > label:has(input:checked) {background: rgba(124,92,255,.28); border-color: #7C5CFF;
  box-shadow: 0 0 14px rgba(124,92,255,.4);}

[data-testid="stChatMessage"] {background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.07);
  border-radius: 18px; padding: .9rem 1.1rem; animation: fadeUp .45s ease both;}

.stButton > button {border-radius: 12px; border: 1px solid rgba(124,92,255,.55); transition: all .2s;}
.stButton > button:hover {transform: translateY(-2px); border-color: #7C5CFF; box-shadow: 0 6px 20px rgba(124,92,255,.4);}

[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 18px;}

.safe {display: inline-block; padding: .3rem .8rem; border-radius: 999px; font-size: .85rem; font-weight: 600;
  background: rgba(52,211,153,.14); border: 1px solid rgba(52,211,153,.55); color: #6EE7B7; animation: pulse 2.2s infinite;}

::-webkit-scrollbar {width: 8px; height: 8px;}
::-webkit-scrollbar-thumb {background: rgba(124,92,255,.5); border-radius: 8px;}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def hero():
    st.markdown(
        '<div class="hero"><div class="hero-row"><span class="logo">💬</span><div>'
        '<h1>Chat Intelligence Platform</h1>'
        '<p>Upload a chat. Talk to AI agents that answer with real messages as proof.</p>'
        '<div class="livetxt"><span class="live"></span>Agents online</div>'
        '</div></div></div>',
        unsafe_allow_html=True,
    )


def section(title, subtitle=""):
    sub = f'<span class="ss">{html.escape(subtitle)}</span>' if subtitle else ""
    st.markdown(
        f'<div class="sec"><div class="bar"></div><div class="tt">{html.escape(title)}</div>{sub}</div>',
        unsafe_allow_html=True,
    )


def chips(items):
    body = "".join(f'<span class="chip">{html.escape(str(i))}</span>' for i in items)
    st.markdown(body, unsafe_allow_html=True)


def badge():
    st.markdown('<span class="safe">✅ Passed safety check</span>', unsafe_allow_html=True)


def card(emoji, title, value, sub, i=0):
    color = COLORS[i % len(COLORS)]
    return (
        f'<div class="wcard" style="--a:{color}; animation-delay:{i * 0.09}s">'
        f'<div class="e">{emoji}</div>'
        f'<div class="t">{html.escape(str(title))}</div>'
        f'<div class="v">{html.escape(str(value))}</div>'
        f'<div class="s">{html.escape(str(sub))}</div></div>'
    )


def wrapped(df):
    d = df.sort_values("ts").reset_index(drop=True)
    cards = []

    vc = d.sender.value_counts()
    cards.append(("👑", "Top talker", vc.index[0], f"{int(vc.iloc[0])} messages"))

    gap = d.ts.diff() > pd.Timedelta(hours=6)
    starters = d[gap | (d.index == 0)].sender.value_counts()
    cards.append(("🚀", "Conversation starter", starters.index[0], f"started {int(starters.iloc[0])} conversations"))

    voice = d[d.is_voice].sender.value_counts()
    if len(voice):
        cards.append(("🎙️", "Voice-note champion", voice.index[0], f"{int(voice.iloc[0])} voice notes"))
    else:
        cards.append(("🎙️", "Voice-note champion", "Nobody", "no voice notes found"))

    hour = d.ts.dt.hour
    late = d.assign(late=(hour >= 23) | (hour < 5)).groupby("sender").late.mean()
    if late.max() > 0:
        cards.append(("🦉", "Night owl", late.idxmax(), f"{round(late.max() * 100)}% of messages after 11 PM"))
    else:
        cards.append(("🦉", "Night owl", "Nobody", "no late-night messages"))

    words = d.assign(w=d.text.str.split().str.len()).groupby("sender").w.mean()
    cards.append(("📝", "Wordiest", words.idxmax(), f"{words.max():.1f} words per message"))

    days = d.ts.dt.date.value_counts()
    cards.append(("🔥", "Busiest day", str(days.index[0]), f"{int(days.iloc[0])} messages"))
    return cards


def pretty(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#C9CEDB",
        showlegend=False,
        margin=dict(t=50, l=10, r=10, b=10),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,.06)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,.06)")
    return fig