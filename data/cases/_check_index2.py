# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\Lin\Desktop\skills\liu-yao")
html = (ROOT / "index.html").read_text(encoding="utf-8")

# extract portal-data
m = re.search(
    r'<script id="portal-data" type="application/json">(.*?)</script>',
    html, flags=re.S,
)
if not m:
    print("FAIL: portal-data block missing")
else:
    raw = m.group(1)
    # undo escape
    raw2 = raw.replace("<\\/", "</")
    try:
        data = json.loads(raw2)
        print("portal-data OK: samples", len(data.get("samples") or []), "avg", data.get("blind", {}).get("avg"))
        s0 = (data.get("samples") or [None])[0]
        if s0:
            print("sample0", s0.get("id"), s0.get("verdict"), "body", len((s0.get("human") or {}).get("body") or []))
            print("lead:", ((s0.get("human") or {}).get("body") or [""])[0][:80])
    except Exception as e:
        print("FAIL json:", e)
        print(raw[:200])

# JS structure checks
for label, needle in [
    ("footer html", "<footer>装卦由"),
    ("IIFE end", "render(samples[0]);"),
    ("script close", "</script>"),
    ("body close", "</body>"),
    ("html close", "</html>"),
]:
    print(f"{label}: {'OK' if needle in html else 'MISSING'}")

# sample reports
for name in ["sample_report_final.html", "sample_report_ZS007.html"]:
    p = ROOT / name
    if not p.exists():
        print(name, "missing")
        continue
    t = p.read_text(encoding="utf-8")
    has_human = "人话" in t
    has_reading = "解读" in t or "六爻" in t
    print(f"{name}: bytes={len(t)} 人话字眼={has_human} switchTab={'switchTab' in t}")
