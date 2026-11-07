import os, time
from dotenv import load_dotenv
from google import genai

load_dotenv()
c = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model = os.getenv("MODEL")
print("Using model:", model)

for attempt in range(1, 6):
    try:
        print(c.models.generate_content(model=model, contents="Say hi in 5 words").text)
        break
    except Exception as e:
        print(f"Attempt {attempt} failed:", str(e)[:120])
        time.sleep(5)