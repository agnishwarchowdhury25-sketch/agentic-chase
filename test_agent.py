from chat_parser import parse
import db, rag, agents

db.init()
df = parse(open("test.txt", encoding="utf-8").read())
cid = db.save_chat("Demo", "test", df)
rag.index_chat(cid, df)

answer, evidence = agents.run_agent("Deep Analyzer", [cid], "Who talks more and what is the mood?")
print("ANSWER:", answer)
print("EVIDENCE:", evidence)

db.delete_chat(cid)
rag.delete_index(cid)