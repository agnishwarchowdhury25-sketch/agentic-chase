# 💬 Agentic Chase: Multi-Agent Chat Intelligence Platform

Upload an exported WhatsApp chat and talk to specialised AI agents that answer using **real messages from the chat as evidence**.

Built for **Agentic Chase '26** (PS 04).

## What it does

- **Projects and chats:** group several chats in one project, each with its own separate memory
- **Auto-detection:** finds participants and tells group chats from one-to-one chats
- **Evidence for every answer:** agent replies cite the real messages they used, and the quotes come from the database, never from the AI's imagination
- **Dashboard:** who talks most, activity by hour, activity over time (no AI needed)
- **Hinglish friendly:** works with chats that mix Hindi and English

## The agents

| Agent | Job |
|---|---|
| **Deep Analyzer** | Finds patterns: who drives the chat, mood over time, key moments |
| **Roaster** | Playful roasts based on real chat habits, with a Mild / Medium / Spicy slider |
| **Reply Giver** | Suggests 3 replies in a chosen person's style |
| **Memory Recall** | Finds specific events, plans and promises |

## How it works

```
WhatsApp .txt → Parser → SQLite (messages)
                       → Chunker → ChromaDB (one collection per chat)
Question → Retrieve relevant chunks + chat stats → Gemini agent
        → Answer + message IDs → Real messages looked up in SQLite → Shown as evidence
```

1. **Parser** (`chat_parser.py`) reads timestamps, senders and multi-line messages
2. **Database** (`db.py`) stores chats and messages and detects group vs personal
3. **Search memory** (`rag.py`) cuts chats into chunks tagged with message IDs and searches them
4. **Agents** (`agents.py`) use one LLM with a different prompt and retrieval for each agent
5. **App** (`app.py`) is the Streamlit interface

## Safety and privacy

- **Roast safety:** a tone slider, a banned-topics list (appearance, family, health, religion, caste, relationships, money and more), and a second AI check on every roast before it is shown
- **Opt-out:** people can be excluded from roasts
- **Isolated memory:** each chat has its own separate search memory
- **Delete anytime:** the Privacy tab removes a chat and its memory
- **Duplicate protection:** the same chat can't be added twice to a project
- **Secrets:** the API key lives in `.env`, which is never uploaded

## Tech stack

Python · Streamlit · SQLite · ChromaDB · Google Gemini API · Pandas · Plotly

## Setup

```bash
git clone https://github.com/agnishwarchowdhury25-sketch/agentic-chase.git
cd agentic-chase
python -m venv venv
venv\Scripts\activate        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```
GEMINI_API_KEY=your_key_here
MODEL=gemini-3.5-flash-lite
```

Run:

```bash
streamlit run app.py
```

## How to use

1. Type a project name, upload a WhatsApp `.txt` export, and click **Process**
2. Check the **Dashboard** tab
3. Open the **Agents** tab, pick an agent, optionally pick a participant, and ask
4. Open **🧾 Evidence** under any answer to see the real messages behind it

A sample chat is included: `group.txt`.

## Roadmap

Not built yet:
- Voice-note transcription
- Image analysis and video summaries
- Persistent per-chat topic and timeline summaries
- Promise Tracker (who promised what, and did they do it)

## Team

## Team

**TEAM INDIA**

- Agnishwar Chowdhury
- Amar Shaw
- Abhishek Kr Singh
- Apurva Kr Singh