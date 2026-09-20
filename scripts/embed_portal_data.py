# -*- coding: utf-8 -*-
from pathlib import Path
import json
import re

ROOT = Path(r"C:\Users\Lin\Desktop\skills\liu-yao")
data = (ROOT / "assets" / "portal_data.json").read_text(encoding="utf-8")
data_escaped = data.replace("</", "<\\/")
html_path = ROOT / "index.html"
html = html_path.read_text(encoding="utf-8")

if "__PORTAL_DATA__" in html:
    html = html.replace("__PORTAL_DATA__", data_escaped, 1)
else:
    html2, n = re.subn(
        r'(<script id="portal-data" type="application/json">)(.*?)(</script>)',
        lambda m: m.group(1) + data_escaped + m.group(3),
        html,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("portal-data script tag not found")
    html = html2

html_path.write_text(html, encoding="utf-8")
print("index.html data refreshed, bytes", len(html))
