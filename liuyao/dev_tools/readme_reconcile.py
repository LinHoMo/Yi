# -*- coding: utf-8 -*-
"""README 关键数字 ↔ ledger 真值 只读对账（第五百三十五批，B）。

CAPABILITY 的「声明↔数据」已由 G12/G13/G14/C1 的 reconcile 门守着；但两份学科 README 也承载
对齐分／top-1／n／维度等对外读数，且 535 巡检发现两处已漏回流（liuyao zengshan 61.8→86.5、
bazi tune/holdout 命令注释 60/278→61/279）。本门把这些 README 关键数字与 `readout_ledger.py`
钉死的权威真值逐一对账，闭环 README 这一层的「声明↔数据」漂移。

守 528 批约定不新增 `check.py` 门号，仿 C1/G12/G13 挂 CI root-gates；不写任何文件。真值取自
`readout_ledger.py` 的断言项（如 `liuyao.zengshan_dz(86.5/48.3)`、`八字案例分母(61/279/69)`、
`bazi.holdout(100.0)`、`bazi.holdout 分维(...)`），ledger 自身已对数据重放，本门是其下游第二道闸。

    python liuyao/dev_tools/readme_reconcile.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent                      # liuyao/dev_tools -> 仓库根
LIUYAO_README = REPO / "liuyao" / "README.md"
BAZI_README = REPO / "bazi" / "README.md"

# 中文 CLI 编码红线（check_cli_encoding 守）：cp936 控制台下也必须交出可读的 UTF-8。
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _table_field(text: str, row_keyword: str, field_index: int):
    """在含 row_keyword 且以 | 开头的表格行里，按 | 切分取第 field_index 字段（1-based）。"""
    for line in text.splitlines():
        if row_keyword in line and line.strip().startswith("|"):
            parts = [c.strip() for c in line.split("|")]
            if len(parts) > field_index:
                return parts[field_index]
    return None


def _num(field, percent: bool = False):
    if field is None:
        return None
    if percent:
        m = re.search(r"\*\*([\d.]+)%\*\*", field)
    else:
        m = re.search(r"\*\*([\d.]+)\*\*|(\d+)", field)
    if not m:
        return None
    val = m.group(1) or m.group(2)
    return float(val)


def _regex_num(text: str, pattern: str):
    m = re.search(pattern, text)
    return float(m.group(1)) if m else None


def _checks():
    """每条：(label, README 声称值 or None, ledger 真值 or None, 容忍差)。
    ledger 真值 = None 表示「存在性」检查（声称值非 None 即过）。"""
    ly = _read(LIUYAO_README)
    bz = _read(BAZI_README)

    return [
        # —— liuyao README：现在真实水平 + 外部集表（对齐分 / top-1 / n）——
        # 真值对应 readout_ledger: liuyao.tune(97.9/64.7/1.53)、liuyao.holdout(90.2/50.0/1.6)、
        # liuyao.wikisource(75.8/31.8/2.03)、liuyao.zengshan_dz(86.5/48.3)、liuyao.bushi_zhengzong(65.3/23.7)
        ("liuyao 对齐分 tune",        _num(_table_field(ly, "tune（", 2), True),        97.9, 0.15),
        ("liuyao 对齐分 holdout",     _num(_table_field(ly, "holdout（", 2), True),     90.2, 0.15),
        ("liuyao 对齐分 wikisource",  _num(_table_field(ly, "wikisource_holdout（", 2), True), 75.8, 0.15),
        ("liuyao 对齐分 zengshan",    _num(_table_field(ly, "zengshan_dz_holdout（", 2), True), 86.5, 0.15),
        ("liuyao 对齐分 bushi",       _num(_table_field(ly, "bushi_zhengzong_holdout（", 2), True), 65.3, 0.15),
        ("liuyao top-1 zengshan",     _num(_table_field(ly, "zengshan_dz_holdout（", 4), True), 48.3, 0.15),
        ("liuyao top-1 wikisource",   _num(_table_field(ly, "wikisource_holdout（", 4), True), 31.8, 0.15),
        ("liuyao top-1 bushi",        _num(_table_field(ly, "bushi_zhengzong_holdout（", 4), True), 23.7, 0.15),
        ("liuyao n tune",             _num(_table_field(ly, "tune（", 3)),            20,   0.0),
        ("liuyao n holdout",          _num(_table_field(ly, "holdout（", 3)),         12,   0.0),
        ("liuyao n wikisource",       _num(_table_field(ly, "wikisource_holdout（", 3)), 50, 0.0),
        ("liuyao n zengshan",         _num(_table_field(ly, "zengshan_dz_holdout（", 3)), 29, 0.0),
        ("liuyao n bushi",            _num(_table_field(ly, "bushi_zhengzong_holdout（", 3)), 38, 0.0),

        # —— bazi README：tune/holdout 的 n（表格 + 命令注释）＋holdout 对齐分 + 维度 ——
        # 真值对应 readout_ledger: 八字案例分母(61/279/69)、bazi.holdout(100.0)、
        # bazi.holdout 分维(213/213×3 51/51 36/36 17/18)
        ("bazi n tune(表格)",         _num(_table_field(bz, "| tune |", 3)),           61,   0.0),
        ("bazi n holdout(表格)",      _num(_table_field(bz, "| holdout |", 3)),        279,  0.0),
        ("bazi n tune(命令注释)",     _regex_num(bz, r"split tune\s+#[^#]*?(\d+)\s*例"),  61,   0.0),
        ("bazi n holdout(命令注释)",  _regex_num(bz, r"split holdout\s+#[^#]*?(\d+)\s*例"), 279, 0.0),
        ("bazi holdout 对齐分",       _num(_table_field(bz, "| holdout |", 2), True),  100.0, 0.15),
        ("bazi holdout dims tiaohou 51/51", 1.0 if re.search(r"tiaohou`\s*51/51", bz) else None, None, 0.0),
        ("bazi holdout dims pattern 36/36",  1.0 if re.search(r"pattern`\s*36/36", bz) else None,  None, 0.0),
        ("bazi holdout dims cong_ge 17/18",  1.0 if re.search(r"cong_ge`\s*\*\*17/18", bz) else None, None, 0.0),
    ]


def reconcile() -> int:
    fails = []
    n = 0
    for label, claimed, expected, tol in _checks():
        n += 1
        if claimed is None:
            fails.append("%s：README 解析失败（ledger 真值 %.2f）" % (label, expected or 0))
            continue
        if expected is None:                      # 存在性检查
            continue
        if abs(claimed - expected) > tol + 1e-9:
            fails.append("%s：README %.2f ≠ ledger 真值 %.2f（差 %.2f > %.2f）"
                         % (label, claimed, expected, abs(claimed - expected), tol))
    if fails:
        print("× README 关键数字对账失败：")
        for f in fails:
            print("  - " + f)
        return 1
    print("√ README 关键数字 ↔ ledger 真值一致（共 %d 项）" % n)
    return 0


def main() -> int:
    force_utf8_stdio()
    if not LIUYAO_README.exists() or not BAZI_README.exists():
        print("× README 文件缺失：%s / %s" % (LIUYAO_README, BAZI_README))
        return 1
    return reconcile()


if __name__ == "__main__":
    sys.exit(main())
