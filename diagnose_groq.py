"""Quick Groq connectivity check. Run:  python diagnose_groq.py"""
import os
from pathlib import Path

# load .env
envf = Path(__file__).parent / ".env"
if envf.exists():
    for line in envf.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

key = os.environ.get("GROQ_API_KEY", "")
model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
print(f"LLM_PROVIDER = {os.environ.get('LLM_PROVIDER')}")
print(f"GROQ_MODEL   = {model}")
print(f"GROQ_API_KEY = {'set, len=' + str(len(key)) if key else 'NOT SET'}")

try:
    from groq import Groq
except Exception as e:
    print("groq SDK import FAILED:", repr(e))
    raise SystemExit(1)

try:
    client = Groq(api_key=key)
    print("\n--- models available to your key ---")
    try:
        for m in sorted(m.id for m in client.models.list().data):
            print("  ", m)
    except Exception as e:
        print("could not list models:", repr(e))

    print("\n--- plain chat ---")
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Reply with exactly: OK"}],
        max_tokens=10, temperature=0,
    )
    print("plain chat OK ->", repr(r.choices[0].message.content))

    print("\n--- json_object chat ---")
    r2 = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Return JSON {\"status\":\"ok\"}"}],
        max_tokens=30, temperature=0,
        response_format={"type": "json_object"},
    )
    print("json chat OK ->", repr(r2.choices[0].message.content))
    print("\nALL GOOD - Groq is reachable and both call styles work.")
except Exception as e:
    import traceback
    print("\nGROQ CALL FAILED:")
    traceback.print_exc()
