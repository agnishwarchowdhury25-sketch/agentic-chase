import sqlite3
import uuid
import pandas as pd

DB = "app.db"

def con():
    return sqlite3.connect(DB)

def init():
    with con() as c:
        c.execute("create table if not exists chats(chat_id text primary key, project text, name text, type text)")

def save_chat(project, name, df):
    chat_id = uuid.uuid4().hex[:6]
    ctype = "personal" if df.sender.nunique() == 2 else "group"
    d = df.copy()
    d["chat_id"] = chat_id
    d["ts"] = d.ts.astype(str)
    with con() as c:
        c.execute("insert into chats values(?,?,?,?)", (chat_id, project, name, ctype))
        d.to_sql("messages", c, if_exists="append", index=False)
    return chat_id

def list_chats():
    with con() as c:
        return pd.read_sql("select * from chats", c).to_dict("records")

def messages(chat_id):
    with con() as c:
        df = pd.read_sql("select * from messages where chat_id=?", c, params=[chat_id])
    df["ts"] = pd.to_datetime(df.ts)
    df["is_media"] = df.is_media.astype(bool)
    df["is_voice"] = df.is_voice.astype(bool)
    return df

def get_message(chat_id, mid):
    with con() as c:
        r = pd.read_sql("select * from messages where chat_id=? and id=?", c, params=[chat_id, int(mid)])
    return r.iloc[0].to_dict() if len(r) else None

def delete_chat(chat_id):
    with con() as c:
        c.execute("delete from messages where chat_id=?", (chat_id,))
        c.execute("delete from chats where chat_id=?", (chat_id,))