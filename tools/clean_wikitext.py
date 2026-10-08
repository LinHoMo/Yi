# -*- coding: utf-8 -*-
"""维基文库 wikitext → 纯文本清洗器。

用法：
  python tools/clean_wikitext.py data/sources/di-tian-sui.wikitext.txt -o modernized/ming/di-tian-sui.txt
  python tools/clean_wikitext.py --all  # 清洗 data/sources/ 下全部文件到 modernized/<学科>/

清洗规则（保守，只做字符级去除，不转写）：
  - 去掉 {{Header}} / {{wikipedia}} / <onlyinclude> / <!-- --> 等维基标记
  - 去掉 == 标题 ==" 的等号但保留标题文字
  - 去掉 {{:epage}} 嵌入标记
  - 合并连续空行、去除行首尾空白（保留段内换行）
  - 首行写入出处元信息（书名/卷次/来源/抓取时刻）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources"
MODERN = ROOT / "modernized"
CST = timezone(timedelta(hours=8))

# key → 学科目录
DISCIPLINE_MAP = {
    "di-tian-sui": "ming",
    "di-tian-sui-chan-wei": "ming",
    "qiong-tong-bao-jian": "ming",
    "shen-feng-tong-kao": "ming",
    "yuan-hai-zi-ping": "ming",
    "zi-wei-dou-shu-quan-shu": "ziwei",
    "zengshan_buyi": "liuyao",
    "huangjin_ce": "liuyao",
    "huozhulin": "liuyao",
    "bushi_zhengzong": "liuyao",
    "mei-hua-yi-shu": "meihua",
    "yuxiaji": "zeji",
    "liu-ren-da-quan": "liurn",
    "liu-ren-zhi-nan": "liurn",
    "ling-qi-jing": "lingqi",
    "yan-bo-diao-sou-ge": "liurn",  # 奇门参考
}

# 殆知阁异源批（key 以 _dz 结尾；详见 tools/fetch_source.py DZ_CATALOG）。
# 对勘本（与维基文库同书）也一并清洗：简体转录本对部分 LLM 更易读，且与繁体本互备。
DZ_DISCIPLINE_MAP = {
    # 六爻/卜筮
    "bushi_zhengzong_dz": "liuyao",
    "bushi_quanshu_dz": "liuyao",
    "yimao_dz": "liuyao",
    "yiin_dz": "liuyao",
    "duanyi_tianji_dz": "liuyao",
    "yilin_buyi_dz": "liuyao",
    "jingshi_yizhuan_dz": "liuyao",
    "zhouyi_shangzhan_dz": "liuyao",
    "wenwang_jinqianke_dz": "liuyao",
    "zengshan_buyi_dz": "liuyao",
    "huangjince_dz": "liuyao",
    "huozhulin_dz": "liuyao",
    # 八字
    "yuanhai_ziping_dz": "ming",
    "ziping_zhenquan_pingzhu_dz": "ming",
    "sanming_tonghui_dz": "ming",
    "lixuzhong_mingshu_dz": "ming",
    "wuxing_jingji_dz": "ming",
    "qianli_minggao_dz": "ming",
    "mingli_tanyuan_dz": "ming",
    "lantai_miaoxuan_dz": "ming",
    "yuzhao_dingzhen_dz": "ming",
    "sanming_zhimi_fu_dz": "ming",
    "qiong_tong_bao_jian_dz": "ming",
    "shenfeng_tongkao_dz": "ming",
    "ditian_sui_chanwei_dz": "ming",
    # 大六壬
    "liuren_xinjing_dz": "liurn",
    "liuren_duanan_dz": "liurn",
    "liuren_cuiyan_dz": "liurn",
    "rengui_dz": "liurn",
    "liuren_zhizhi_yuding_dz": "liurn",
    "liuren_shending_dz": "liurn",
    "liuren_zhinan_dz": "liurn",
    # 择吉
    "xieji_bianfang_dz": "zeji",
    "xingli_kaoyuan_dz": "zeji",
    # 奇门/太乙（仓库无对应学科，单列参考库；烟波钓叟歌先例归 liurn 不再重复）
    "dunjia_yanyi_dz": "qimen",
    "qimen_baojian_dz": "qimen",
    "qimen_tongzong_dz": "qimen",
    "qimen_faqiao_dz": "qimen",
    "taiyi_jinjing_dz": "taiyi",
    "taiyi_mishu_dz": "taiyi",
    # 通纲 / 易占 / 杂占
    "wuxing_dayi_dz": "tonglun",
    "huangji_jingshi_shu_dz": "tonglun",
    "jiaoshi_yilin_dz": "yizhan",
    "tuibeitu_dz": "yizhan",
    "zhougong_jiemeng_dz": "yizhan",
    "cezi_midie_dz": "yizhan",
    "zhuge_shenshu_dz": "yizhan",
    "yizhangjing_dz": "yizhan",
    # 梅花 / 灵棋对勘
    "meihua_yishu_dz": "meihua",
    "lingqijing_dz": "lingqi",
}


def clean(text: str) -> str:
    """保守清洗维基标记，保留正文文字。"""
    # 去掉 HTML 注释
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # 去掉 <onlyinclude>...</onlyinclude> 与同名自闭标签
    text = re.sub(r"</?onlyinclude>", "", text)
    # 去掉 {{Header|title=...}} 整行维基模板
    text = re.sub(r"\{\{Header\|[^}]*\}\}", "", text)
    # 去掉 {{wikipedia}}
    text = re.sub(r"\{\{wikipedia\}\}", "", text, flags=re.IGNORECASE)
    # 去掉 {{:epage}} 嵌入标记
    text = re.sub(r"\{\{:[^}]*\}\}", "", text)
    # 把 ==标题==（含 = 号层级）的等号剥掉但保留文字
    def strip_equals(m):
        inner = m.group(1)
        inner = re.sub(r"^=+\s*", "", inner)
        inner = re.sub(r"\s*=+$", "", inner)
        return inner.strip()
    text = re.sub(r"={2,6}\s*(.*?)\s*={2,6}", strip_equals, text)
    # 去 ''' 与 '' 加粗斜体标记
    text = re.sub(r"'''''([^']+)''''*", r"\1", text)
    text = re.sub(r"'''([^']+)'''", r"\1", text)
    text = re.sub(r"''([^']+)''", r"\1", text)
    # 去内部维基链接 [[A|B]] → B，[[A]] → A
    text = re.sub(r"\[\[[^|\]]*\|([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]*)\]\]", r"\1", text)
    # 去 __TOC__ 等魔术字
    text = re.sub(r"__[A-Z_]+__", "", text)
    # 去除每行首尾空白
    lines = [ln.strip() for ln in text.splitlines()]
    # 合并连续空行
    out = []
    prev_blank = False
    for ln in lines:
        if not ln:
            if prev_blank:
                continue
            prev_blank = True
        else:
            prev_blank = False
        out.append(ln)
    # 去掉首尾空行
    while out and not out[0]:
        out.pop(0)
    while out and not out[-1]:
        out.pop()
    return "\n".join(out)


def provenance_for(src: Path) -> dict:
    prov = src.with_suffix("").with_suffix(".provenance.json")
    if prov.exists():
        try:
            return json.loads(prov.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def split_key_stem(stem: str) -> tuple[str, bool]:
    """'x.dz' → ('x', True)；'x.wikitext' → ('x', False)；其余原样。"""
    if stem.endswith(".dz"):
        return stem[:-3], True
    if stem.endswith(".wikitext"):
        return stem[:-9], False
    return stem, False


def process_one(src: Path, out_dir: Path) -> Path | None:
    raw = src.read_text(encoding="utf-8")
    cleaned = clean(raw)
    key, is_dz = split_key_stem(src.stem)
    prov = provenance_for(src)

    if is_dz:
        site = ("殆知阁古代文献 v2.0（github.com/garychowcmu/daizhigev20，"
                "志愿转录简体、未经专业校勘；同书维基文库本见 modernized/ 同科目录）")
    else:
        site = "维基文库 https://zh.wikisource.org（繁体志愿转录）"
    meta = (
        f"# {key}\n"
        f"# 来源：{site}\n"
        f"# 出处：{prov.get('title', key)}\n"
        f"# 字节：{prov.get('stats', {}).get('bytes', len(raw.encode('utf-8')))}\n"
        f"# sha256：{prov.get('sha256', 'N/A')}\n"
        f"# 清洗时刻：{datetime.now(CST).isoformat(timespec='seconds')}\n"
        f"#\n"
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{key}.txt"
    out.write_text(meta + "\n" + cleaned, encoding="utf-8")
    rel = out.relative_to(ROOT)
    print(f"  ✓ {src.name} → {rel} ({len(cleaned)} chars)")
    return out


def main():
    ap = argparse.ArgumentParser(description="清洗维基文库 wikitext 为纯文本")
    ap.add_argument("input", nargs="?", help="输入 .wikitext.txt 文件")
    ap.add_argument("-o", "--output", help="输出文件路径")
    ap.add_argument("--all", action="store_true", help="清洗 data/sources/ 下全部到 modernized/<学科>/")
    args = ap.parse_args()

    if args.all:
        files = sorted(SOURCES.glob("*.wikitext.txt")) + sorted(SOURCES.glob("*.dz.txt"))
        print(f"共 {len(files)} 个源文件：")
        count = 0
        for f in files:
            key, is_dz = split_key_stem(f.stem)
            # 多卷本：liu-ren-da-quan-juanN → 归 liurn 并用同一主 key 前缀
            base_key = re.sub(r"-juan\d+$", "", key)
            disc = (DISCIPLINE_MAP.get(key) or DZ_DISCIPLINE_MAP.get(key)
                    or DISCIPLINE_MAP.get(base_key, "liuyao"))
            out_dir = MODERN / disc
            process_one(f, out_dir)
            count += 1
        print(f"\n已处理 {count} 个文件。")
        return

    if not args.input:
        ap.error("请指定输入文件或使用 --all")
        return
    src = Path(args.input)
    key, _ = split_key_stem(src.stem)
    disc = (DISCIPLINE_MAP.get(key) or DZ_DISCIPLINE_MAP.get(key, "liuyao"))
    out_dir = MODERN / disc
    if args.output:
        out_dir = Path(args.output)
    process_one(src, out_dir)


if __name__ == "__main__":
    main()
