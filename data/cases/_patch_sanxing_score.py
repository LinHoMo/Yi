# -*- coding: utf-8 -*-
"""P0-4d 三刑逐条 score 字段（供 step3 按用神参与过滤）"""
import io, re

PATH = r'C:\Users\Lin\Desktop\skills\liu-yao\scripts\classical_analysis.py'
with io.open(PATH, 'r', encoding='utf-8') as f:
    src = f.read()

# 逐段加 score 字段
replacements = [
    # 循环刑：完整
    ('''                "description": (
                    f"{ptype}（完整三刑）：{present[0]}刑{present[1]}刑{present[2]}，"
                    f"三字全见于{ '、'.join(pos_list) }，极凶之象"
                ),
            })
            total_score -= 1.0''',
     '''                "description": (
                    f"{ptype}（完整三刑）：{present[0]}刑{present[1]}刑{present[2]}，"
                    f"三字全见于{ '、'.join(pos_list) }，极凶之象"
                ),
                "score": -1.0,
            })
            total_score -= 1.0'''),
    # 循环刑：催刑
    ('''                "description": (
                    f"{ptype}（催刑）：卦内{ '、'.join(p for p in present if p in hex_set) or '无'}，"
                    f"月日{ '、'.join(p for p in present if p not in hex_set) }补足成刑，"
                    f"刑伤力减半"
                ),
            })
            total_score -= 0.5''',
     '''                "description": (
                    f"{ptype}（催刑）：卦内{ '、'.join(p for p in present if p in hex_set) or '无'}，"
                    f"月日{ '、'.join(p for p in present if p not in hex_set) }补足成刑，"
                    f"刑伤力减半"
                ),
                "score": -0.5,
            })
            total_score -= 0.5'''),
    # 循环刑：待刑
    ('''                "description": (
                    f"{ptype}（待刑）：{present[0]}、{present[1]}相见，"
                    f"缺{missing[0]}，待月日逢{missing[0]}方成刑，"
                    f"目前刑伤未全，但有刑伤之象"
                ),
            })
            total_score -= 0.3''',
     '''                "description": (
                    f"{ptype}（待刑）：{present[0]}、{present[1]}相见，"
                    f"缺{missing[0]}，待月日逢{missing[0]}方成刑，"
                    f"目前刑伤未全，但有刑伤之象"
                ),
                "score": -0.3,
            })
            total_score -= 0.3'''),
    # 互刑：成刑
    ('''                "description": (
                    f"无礼之刑（成刑）：{b1_key}刑{b2_key}，"
                    f"见于{ '、'.join(pos_list) }，主无礼刑伤、恩中之怨"
                ),
            })
            total_score -= 0.5''',
     '''                "description": (
                    f"无礼之刑（成刑）：{b1_key}刑{b2_key}，"
                    f"见于{ '、'.join(pos_list) }，主无礼刑伤、恩中之怨"
                ),
                "score": -0.5,
            })
            total_score -= 0.5'''),
    # 互刑：待刑
    ('''                "description": (
                    f"无礼之刑（待刑）：{b1_key}、{b2_key}月日相见，"
                    f"刑伤未全，主微咎"
                ),
            })
            total_score -= 0.3''',
     '''                "description": (
                    f"无礼之刑（待刑）：{b1_key}、{b2_key}月日相见，"
                    f"刑伤未全，主微咎"
                ),
                "score": -0.3,
            })
            total_score -= 0.3'''),
    # 自刑
    ('''                "description": (
                    f"自刑：{sp_branch}出现{count}次"
                    f"（{ '、'.join(pos_list) }），"
                    f"自刑主自我纠结、自作自受、内心矛盾"
                ),
            })
            total_score -= 0.3 * (count - 1)  # 每多一次减0.3''',
     '''                "description": (
                    f"自刑：{sp_branch}出现{count}次"
                    f"（{ '、'.join(pos_list) }），"
                    f"自刑主自我纠结、自作自受、内心矛盾"
                ),
                "score": -0.3 * (count - 1),
            })
            total_score -= 0.3 * (count - 1)  # 每多一次减0.3'''),
]

for old, new in replacements:
    assert old in src, f"未找到段: {old[:60]}..."
    src = src.replace(old, new, 1)

with io.open(PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)

print("OK: 三刑逐条 score 已加入")
