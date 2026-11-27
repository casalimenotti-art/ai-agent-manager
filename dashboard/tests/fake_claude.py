#!/usr/bin/env python3
"""Finto `claude` per i test: legge il prompt da stdin, emette stream-json."""
import json, sys
prompt = sys.stdin.read()
args = sys.argv[1:]
sid = args[args.index("--resume") + 1] if "--resume" in args else "sess-nuova"
out = lambda o: print(json.dumps(o), flush=True)
out({"type": "system", "subtype": "init", "session_id": sid})
for parola in ("Ciao ", "da ", "fake: ", prompt.strip()[:20]):
    out({"type": "stream_event", "session_id": sid, "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": parola}}})
out({"type": "assistant", "session_id": sid, "message": {"content": [{"type": "tool_use", "name": "Read"}]}})
out({"type": "result", "session_id": sid, "result": "Ciao da fake", "total_cost_usd": 0.01, "is_error": False})
