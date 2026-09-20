# -*- coding: utf-8 -*-
from pathlib import Path
p = Path(r"C:\Users\Lin\Desktop\skills\liu-yao\index.html")
t = p.read_text(encoding="utf-8")
print("len", len(t), "lines", t.count("\n") + 1)
print("script open", t.count("<script"), "close", t.count("</script>"))
print("portal-data", t.count('id="portal-data"'))
print("--- tail ---")
print(repr(t[-500:]))
print("--- around footer ---")
i = t.find("装卦由")
print(repr(t[i:i+300]) if i >= 0 else "footer not found")
