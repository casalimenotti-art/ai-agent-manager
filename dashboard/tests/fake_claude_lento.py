#!/usr/bin/env python3
"""Finto claude per i test delle chat parallele: «lento…» resta in attesa a lungo, altrimenti impiega 1 s e risponde con il prompt."""
import json, sys, time
prompt = sys.stdin.read().strip()
args = sys.argv[1:]
sid = args[args.index("--resume") + 1] if "--resume" in args else "s-" + str(abs(hash(prompt)) % 10000)
out = lambda o: print(json.dumps(o), flush=True)
out({"type": "system", "subtype": "init", "session_id": sid})
if prompt.startswith("lento"):
    for i in range(120):
        out({"type": "stream_event", "session_id": sid, "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "." }}})
        time.sleep(0.5)
else:
    time.sleep(1.0)
    out({"type": "stream_event", "session_id": sid, "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Risposta a: " + prompt}}})
    out({"type": "assistant", "session_id": sid, "message": {"content": [{"type": "tool_use", "name": "WebSearch"}]}})
out({"type": "result", "session_id": sid, "result": "Risposta a: " + prompt, "total_cost_usd": 0.01, "is_error": False})
