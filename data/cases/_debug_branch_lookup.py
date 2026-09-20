# -*- coding: utf-8 -*-
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from thinking_chain import get_changed_hexagram_branch, HEXAGRAM_TRIGRAMS
print("讼 in TRIGRAMS", "讼" in HEXAGRAM_TRIGRAMS)
print("branch pos1 of 讼", get_changed_hexagram_branch("讼", 1))
print("branch pos4 of 讼", get_changed_hexagram_branch("讼", 4))
