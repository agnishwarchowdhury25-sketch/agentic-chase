import os
import re
import json
import time
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
import db
import rag

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("MODEL")


def llm(system, user, as_json=False):
    cfg = types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json" if as_json else "text/plain",
    )
    last = None
    for attempt in range(5):
        try:
            r = client.models.generate_content(model=MODEL, contents=user, config=cfg)
            return r.text or ""
        except Exception as e:
            last = e
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"AI is busy or unreachable: {str(last)[:150]}")


def llm_json(system, user):
    t = llm(system + "\nReturn ONLY valid JSON.", user, as_json=True)
    try:
        data = json.loads(t)
    except Exception:
        m = re.search(r"(\{.*\}|\[.*\])", t, re.S)
        try:
            data = json.loads(m.group(0))
        except Exception:
            return {"answer": t, "evidence": []}
    if isinstance(data, list):
        answers, evidence = [], []
        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                answers.append(f"{i}. {item.get('answer', '')}")
                evidence += item.get("evidence", [])
            else:
                answers.append(f"{i}. {item}")
        return {"answer": "\n\n".join(answers), "evidence": list(dict.fromkeys(evidence))}
    if not isinstance(data, dict):
        return {"answer": str(data), "evidence": []}
    return data


def stats(df):
    gap = df.ts.diff() > pd.Timedelta(hours=6)
    return {
        "messages_per_person": df.sender.value_counts().to_dict(),
        "avg_words_per_message": df.assign(w=df.text.str.split().str.len()).groupby("sender").w.mean().round(1).to_dict(),
        "conversation_starters": df[gap | (df.index == 0)].sender.value_counts().to_dict(),
        "voice_notes": df[df.is_voice].sender.value_counts().to_dict(),
        "media_sent": df[df.is_media].sender.value_counts().to_dict(),
        "usual_hour": df.groupby("sender").ts.apply(lambda x: int(x.dt.hour.mode()[0])).to_dict(),
        "messages_per_month": {str(k): int(v) for k, v in df.groupby(df.ts.dt.to_period("M")).size().items()},
    }


BANNED = "appearance/body, family, health, religion, caste, race, gender, sexuality, relationships/breakups, money problems, anything private or traumatic"
TONES = {
    "Mild": "Light teasing only. Friendly and wholesome, like a friend joking.",
    "Medium": "Sarcastic and witty, but never mean.",
    "Spicy": "Sharp, savage humour about chat habits only (reply speed, voice notes, spam, slang). Still never cruel.",
}


def is_safe(text):
    v = llm(
        "You are a strict content safety checker.",
        f"Does this roast touch any of these topics: {BANNED}, or contain abuse or harassment? Answer only SAFE or UNSAFE.\n\n{text}",
    )
    return "UNSAFE" not in v.upper()


def persona(chat_id, person):
    df = db.messages(chat_id)
    msgs = df[(df.sender == person) & (~df.is_media)].text.tolist()
    sample = "\n".join(msgs[::max(1, len(msgs) // 80)][:80])
    return llm_json(
        "You profile people from their chat messages.",
        f'Person: {person}\nMessages:\n{sample}\n\nReturn JSON: {{"style":"","interests":"","humour":"","role_in_group":"","catchphrases":[""],"quirks":""}}',
    )


SYSTEM = {
    "Deep Analyzer": "You analyse chat conversations: who drives them, mood and sentiment over time, key moments, activity patterns. Use the STATS for numbers and the CHAT EXCERPTS for qualitative claims. Never invent facts.",
    "Roaster": "You are a playful roast comedian. Roast ONLY using real habits visible in the STATS and CHAT EXCERPTS. Be funny and specific. Never touch banned topics.",
    "Reply Giver": "You suggest replies to a message. Give exactly 3 options in the requested style. Mimic the person's message length, slang, emoji use and language mix, including Hinglish if used.",
    "Memory Recall": "You find specific events, plans, promises and past discussions. If the excerpts do not contain it, say you could not find it. Never guess.",
}


def run_agent(agent, chat_ids, question, person=None, tone="Mild", optout=()):
    ctx, st = [], {}
    for cid in chat_ids:
        df = db.messages(cid)
        st[cid] = stats(df)
        q = question + (f" {person}" if person else "")
        ctx += rag.retrieve(cid, q, spread=(agent == "Deep Analyzer"))

    persona_txt = ""
    if person and agent in ("Roaster", "Reply Giver"):
        persona_txt = f"\nPERSONA of {person}: {json.dumps(persona(chat_ids[0], person))}"

    extra = ""
    if agent == "Roaster":
        extra = (
            f"\nTONE: {TONES[tone]}\nBANNED TOPICS: {BANNED}"
            f"\nDo NOT roast: {', '.join(optout) or 'nobody opted out'}."
            f"\nTarget: {person or 'whoever fits the question'}."
        )

    prompt = f"""STATS: {json.dumps(st, default=str)}{persona_txt}

CHAT EXCERPTS (each line starts with a [citation-id]):
{chr(10).join(ctx)}
{extra}

USER REQUEST: {question}

Reply as ONE JSON object: {{"answer": "<your full answer, put all options inside this one text>", "evidence": ["<citation-id>", ...]}}
Only list citation-ids of lines that truly support your answer (max 6). If nothing supports it, use an empty list."""

    out = llm_json(SYSTEM[agent], prompt)

    if agent == "Roaster" and not is_safe(out.get("answer", "")):
        out = llm_json(SYSTEM[agent], prompt + "\nYour previous attempt was unsafe. Make it gentler and avoid banned topics.")
        if not is_safe(out.get("answer", "")):
            out["answer"] = "⚠️ Couldn't generate a safe roast for this request. Try a different person or a milder tone."
            out["evidence"] = []

    ev = []
    for e in out.get("evidence", []):
        try:
            cid, mid = str(e).strip("[]").rsplit("-", 1)
            m = db.get_message(cid, mid)
            if m:
                ev.append(f"**{m['sender']}** ({m['ts']}): {m['text']}")
        except Exception:
            pass
    return out.get("answer", ""), ev