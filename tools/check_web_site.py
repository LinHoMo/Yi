# -*- coding: utf-8 -*-
"""站点自检：构建出来的 `_site/` 是否真的能跑。

    python tools/check_web_site.py --site _site

检查项（全绿才算站点可用）：
  1. 前端四件套齐全（index.html / web.css / web.js / engine_runtime.py）
  2. manifest.json 可解析、schema 对得上、学科元数据齐全
  3. **清单与磁盘逐条对齐**：清单里每个文件的 sha256 与字节数与实际文件一致
     （防止"清单说有、盘上没有"以及构建后又改了源文件）
  4. 八科的运行期文件（code + doc，含 core）都在盘上——缺一个页面就报错
  5. `.nojekyll` 存在（否则 Jekyll 会吃掉 `_` 开头的路径与部分 .py）
  6. `engine_runtime.py` 里引用的内核 API 在镜像的 core 里确实存在
     （防止改名之后站点静默失效）
  7. **学科集合同口径**：`manifest.disciplines`（构建期 `DISCIPLINE_META`）与镜像里
     `engine_runtime.py` 的 `WEB_DISCIPLINES` 必须逐项相同——llms.txt（权威表）声称
     这两者同口径，这句得由门看住，而不是靠注释。

零第三方依赖，可在干净 runner 上直接运行。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from yishu_core.runtime import force_utf8_stdio  # noqa: E402

WEB_FILES = ("index.html", "web.css", "web.js", "engine_runtime.py", "favicon.svg")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def check(site: Path) -> list[str]:
    fails: list[str] = []

    for name in WEB_FILES:
        if not (site / name).is_file():
            fails.append(f"缺前端文件 {name}")

    if not (site / ".nojekyll").is_file():
        fails.append("缺 .nojekyll（Jekyll 会吃掉 _ 开头路径）")

    manifest_p = site / "manifest.json"
    if not manifest_p.is_file():
        fails.append("缺 manifest.json")
        return fails
    manifest = json.loads(manifest_p.read_text(encoding="utf-8"))

    if manifest.get("schema") != "yi-web-manifest/1":
        fails.append(f"manifest.schema 不是 yi-web-manifest/1：{manifest.get('schema')!r}")
    if not manifest.get("engine_root"):
        fails.append("manifest.engine_root 为空")
    discs = [d.get("id") for d in manifest.get("disciplines") or []]
    if not discs:
        fails.append("manifest.disciplines 为空")

    files = manifest.get("files") or []
    if not files:
        fails.append("manifest.files 为空")

    # 3) 清单 ↔ 磁盘逐条对齐
    missing = mismatched = 0
    for f in files:
        p = site / f["path"]
        if not p.is_file():
            missing += 1
            if missing <= 5:
                fails.append(f"清单有、盘上没有：{f['path']}")
            continue
        if p.stat().st_size != f["bytes"] or sha256_of(p) != f["sha256"]:
            mismatched += 1
            if mismatched <= 5:
                fails.append(f"清单与文件不一致（改过源码后忘了重新构建？）：{f['path']}")
    if missing > 5:
        fails.append(f"…另有 {missing - 5} 个文件缺失")
    if mismatched > 5:
        fails.append(f"…另有 {mismatched - 5} 个文件不一致")
    if not missing and not mismatched:
        print(f"  √ 清单与镜像逐条对齐（{len(files)} 个文件）")

    # 4) 每科运行期文件齐全
    by_disc: dict[str, list[dict]] = {}
    for f in files:
        d = f.get("discipline")
        if d:
            by_disc.setdefault(d, []).append(f)
    for disc in discs:
        group = by_disc.get(disc) or []
        if not group:
            fails.append(f"{disc}：清单里没有任何文件")
            continue
        scripts = [f for f in group if f.get("runtime")]
        if len(scripts) < 3:
            fails.append(f"{disc}：运行期脚本只有 {len(scripts)} 个（四段契约至少 3 个）")
    core_files = by_disc.get("*") or []
    if len(core_files) < 8:
        fails.append(f"内核文件只有 {len(core_files)} 个——镜像不完整")
    else:
        print(f"  √ 各科运行期文件齐全（内核 {len(core_files)} 个；"
              f"共 {len(discs)} 科）")

    # 6) 前端引用的内核 API 必须在镜像里存在
    rt = (site / "engine_runtime.py")
    if rt.is_file():
        src = rt.read_text(encoding="utf-8")
        imports = re.findall(r"from\s+(yishu_core[\w.]*)\s+import\s+\(?([^)\n]+)", src)
        for mod, names in imports:
            rel = mod.replace(".", "/") + ".py"
            cands = [site / "engine" / "core" / rel,
                     site / "engine" / "core" / mod.split(".")[0] / "__init__.py"]
            if not any(c.is_file() for c in cands):
                fails.append(f"engine_runtime.py 引用的 {mod} 不在镜像里（{rel}）")
                continue
            blob = "\n".join(c.read_text(encoding="utf-8") for c in cands if c.is_file())
            for raw in names.replace("\n", " ").split(","):
                # 去掉行内注释（如 `# noqa: E402`）与非标识符噪声
                token = raw.split("#")[0].strip().split(" as ")[0].strip()
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
                    continue
                if not re.search(rf"\b{re.escape(token)}\b", blob):
                    pkg = site / "engine" / "core" / "yishu_core" / "report" / "__init__.py"
                    if pkg.is_file() and re.search(rf"\b{re.escape(token)}\b",
                                                   pkg.read_text(encoding="utf-8")):
                        continue
                    fails.append(f"engine_runtime.py 用到 {mod}.{token}，镜像里找不到")

    # 7) 学科集合同口径：manifest.disciplines ≡ engine_runtime.WEB_DISCIPLINES
    if rt.is_file():
        text = rt.read_text(encoding="utf-8")
        m = re.search(r"^WEB_DISCIPLINES\s*=\s*\(([^)]*)\)", text, re.M)
        if not m:
            fails.append("engine_runtime.py 里找不到 WEB_DISCIPLINES 元组")
        else:
            web_ids = re.findall(r"[\"']([\w.-]+)[\"']", m.group(1))
            if tuple(web_ids) != tuple(discs):
                fails.append(
                    "学科集合不同口径：manifest.disciplines=[%s] 与 "
                    "engine_runtime.WEB_DISCIPLINES=[%s]（改矩阵时两处必须同步）"
                    % ("、".join(discs), "、".join(web_ids)))
            else:
                print(f"  √ 学科集合同口径（清单与 engine_runtime 均 {len(discs)} 科："
                      f"{'、'.join(discs)}）")

    return fails


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="Yi 站点自检")
    ap.add_argument("--site", type=Path, default=ROOT / "site", help="站点目录")
    args = ap.parse_args()
    site = args.site.resolve()
    if not site.is_dir():
        print(f"× 站点目录不存在：{site}")
        print("  先跑：python tools/build_web.py --outdir site")
        return 2

    print(f"站点自检：{site}")
    fails = check(site)
    if fails:
        print(f"\n× 失败 {len(fails)} 项：")
        for f in fails:
            print("    · " + f)
        return 1
    print("\n√ 站点自检全部通过：页面、清单、镜像、内核 API 引用一致。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
