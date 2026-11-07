import re
import pandas as pd

LINE = re.compile(r'^\[?(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?\s?(?:[APap]\.?[Mm]\.?)?)\]?\s*-?\s*([^:]{1,60}?):\s(.*)$')
MEDIA = re.compile(r'<Media omitted>|\(file attached\)|image omitted|audio omitted|video omitted', re.I)

def parse(text):
    text = text.replace('\u202f', ' ').replace('\u200e', '')
    rows = []
    for line in text.splitlines():
        m = LINE.match(line)
        if m:
            rows.append([m[1] + ' ' + m[2], m[3].strip(), m[4]])
        elif rows and line.strip():
            rows[-1][2] += "\n" + line
    df = pd.DataFrame(rows, columns=["ts", "sender", "text"])
    df["ts"] = pd.to_datetime(df.ts, dayfirst=True, errors="coerce")
    df = df.dropna(subset=["ts"]).reset_index(drop=True)
    df["id"] = df.index
    df["is_media"] = df.text.str.contains(MEDIA)
    df["is_voice"] = df.text.str.contains(r'PTT-|\.opus|audio omitted', case=False, regex=True)
    return df