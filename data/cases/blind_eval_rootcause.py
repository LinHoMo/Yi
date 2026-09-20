# -*- coding: utf-8 -*-
import json, re
from pathlib import Path

BASE_FILE = str(Path(__file__).parent / "classical_cases.json")
ENG_FILE  = str(Path(__file__).parent / "blind_engine_output_v4.json")

with open(BASE_FILE, encoding="utf-8") as f:
    base = json.load(f)
with open(ENG_FILE, encoding="utf-8") as f:
    eng = json.load(f)

base_cases = base["cases"][:20]
eng_cases  = eng["cases"]

results = []
all_scores = []

# Quick recap scores
ZS001=90;ZS002=36;ZS003=32;ZS004=50;ZS005=68;ZS006=86;ZS007=78;ZS008=86
ZS009=68;ZS010=40;ZS011=68;ZS012=40;ZS013=78;ZS014=36;ZS015=36;ZS016=43
ZS017=72;ZS018=83;ZS019=80;ZS020=80
all_scores=[ZS001,ZS002,ZS003,ZS004,ZS005,ZS006,ZS007,ZS008,ZS009,ZS010,ZS011,ZS012,ZS013,ZS014,ZS015,ZS016,ZS017,ZS018,ZS019,ZS020]
avg = sum(all_scores)/len(all_scores)

under70_ids = []
for cid in ["ZS002","ZS003","ZS004","ZS005","ZS009","ZS010","ZS011","ZS012","ZS014","ZS015","ZS016"]:
    idx = int(cid[2:]) - 1
    b = base_cases[idx]
    e = eng_cases[idx]
    under70_ids.append((idx, cid, b, e))

print("=" * 90)
print(" blind evaluation root cause report v4 -- 11 cases < 70 points")
print("=" * 90)
print()
print(f" overall score: {avg:.1f}% (target >= 90%)")
print(f" scores: {all_scores}")
print()

for idx, cid, b, e in under70_ids:
    x_branch = b["expected"].get("use_god_branch", "")
    e_branch = e.get("use_god_branch", "")
    x_use = b["expected"].get("use_god", "")
    e_use = e.get("use_god_category", "")
    x_verdict = b["expected"]["verdict"]
    e_verdict = e["verdict"]

    print("=" * 90)
    print(f" ### {idx+1}. {cid} -- {b['input']['question']}")
    print(f"     expected: use_god={x_use}@{x_branch} verdict={x_verdict}")
    print(f"     engine:   use_god={e_use}@{e_branch} verdict={e_verdict}")
    print(f"     expected key_patterns: {b['expected'].get('key_points',[])}")
    print(f"     engine pattern_tags: {e.get('pattern_tags',[])}")
    print(f"     engine reasoning_chain (last 2): {e.get('reasoning_chain',[])[-2:]}")
    print()

print("=" * 90)
print(" root cause clustering and fix suggestions")
print("=" * 90)
print()

rc = """
[ERROR CATEGORY 1] FU SHEN (伏神) BRANCH LOOKUP FAILURE (4 cases)
------------------------------------------------------------------------
Affected: ZS003, ZS014, ZS015, ZS016 -- all score < 50
Pattern: engine outputs use_god_branch = "?" (missing)
Impact:   subsequent yingqi chain collapses because no branch fixpoint

ZS003: Ge (革) hexagram -- ben gong (本宫) is Li (离), line-2 should
       conceal Wu (午) as wife/wealth (妻财). Engine misses fu shen retrieval.
       Baseline: USE_GOD = WIFE@WU, verdict=吉 (will return, delayed)
       Engine:   USE_GOD = WIFE@?, verdict=凶 (WRONG + direction reversed)

ZS014: Jian (蹇) hexagram -- line-2 should conceal Mao (卯) as wife/wealth.
       Baseline: USE_GOD = WIFE@MAO, verdict=凶 (captured/blocked by flying Shen)
       Engine:   USE_GOD = WIFE@?, verdict=吉 (WRONG)

ZS015: Ji Ji (既济) hexagram -- line-? fu shen Wu (午) concealed under Hai (亥).
       Baseline: USE_GOD = WIFE@WU, verdict=下跌 (price drops, fu blocked + Ji)
       Engine:   USE_GOD = WIFE@?, verdict=吉 (WRONG + reversed)

ZS016: Sheng (升) hexagram -- line-? fu shen Wu (Wu) under Chou (Chou), Chou is empty.
       Baseline: USE_GOD = SON@WU, verdict=吉 (chou empty -> fu emerges -> cure)
       Engine:   USE_GOD = SON@?, verdict=凶 (WRONG + reversed)

FIX P0-A: Strengthen the fu shen retrieval module. When the hexagram lines
          do not contain the required six-relation, the engine must retrieve
          the ben gong (本宫) lines and place them correctly. Verify for
          all 8 hexagram palaces (八宫):
          Qian/Dui/Li/Zhen = lower-inner same as ben gong
          Xun/Kan/Gen/Kun = lower-inner reversed from ben gong
          Line-2 concealment follows standard Fu Shen rules from
          "Zengshan Bu Yi" (增删卜易) chapter on fu shen.

--------------------------------------------------------------------------------

[ERROR CATEGORY 2] USE_GOD BRANCH PRIORITY WRONG (3 cases)
------------------------------------------------------------------------
Affected: ZS005, ZS009, ZS011 -- score 68 each
Pattern: Two use_god candidates in same hexagram (两现), engine picks wrong one

ZS005: Heng (恒) hexagram, lines: initial=Chou, 4th=Xu (妻财)
       Moving line: 4th (Zisun Wu, 子孙午).
       Baseline uses XU (戌, moving line + covered by巳 hui tou sheng).
       Engine picks CHU (chu, initial line, static -> wrong branch).
       Critical: "hui tou sheng" (回头生) pattern not detected.

ZS019: Xun (巽)->Song (讼), lines: initial.Chou + 4th.Wei (妻财)
       Both static (no movement); baseline key pattern is
       "Wei transformed to Wu -> hui tou sheng he" (未化午回头生合).
       Engine picks Chu (wrong) -> pattern mismatch.

FIX P0-B: Priority rule for "two present use_god" (两现):
  1) If one moving, one static -> pick the moving one (rule #1 classic)
  2) If both stationary -> pick the one receiving beneficial
     transformation (hui tou sheng > hui tou ke)
  3) If both equal -> pick the palace-appropriate position

--------------------------------------------------------------------------------

[ERROR CATEGORY 3] ADVANCED PATTERN MISSING IN ENGINE (3 cases)
------------------------------------------------------------------------
Affected: ZS010 (冲中逢合), ZS012 (合处逢冲), ZS016 (飞空得出)
All score < 45

ZS010: Kun (坤) hexagram, 6-chong (六冲) baseline.
       + Day Xu (戌) combines with ying-line (应爻)
       + Day Chen (辰) combines with shi-line (世爻)
       => chong zhong feng he (冲中逢合) = after initial difficulty -> success
       Engine: pattern_tags=[], verdict=大凶 (kills the case)

ZS012: Fou (否) hexagram, 6-he (六合) baseline.
       + Day Chong (日冲) shi line
       + Month Po (月破) ying line
       => he chu feng chong (合处逢冲) = union after reunion fails
       Engine: verdict=吉 (WRONG + reversed)

ZS016: Sheng (升) hexagram.
       + Flying shen Chou (丑) is xunkong (旬空)
       + Fu shen Wu (午) under Chou
       => Fei kong de chu (飞空得出) = fu emerges because flying is empty
       Engine: verdict=凶 (should be 吉)

FIX P0-C: Implement three classic high-level patterns:
  A) "Chong zhong feng he" (冲中逢合):
     Detected: Liu-chong hexagram (六冲卦)
                AND (Day combines shi OR ying OR use_god)
     Override: initial verdict=凶 -> reconcile to verdict=吉, with
               pre-condition "first difficult then succeed"

  B) "He chu feng chong" (合处逢冲):
     Detected: Liu-he hexagram (六合卦)
                AND (Day chong shi OR Month po ying)
     Override: initial verdict=吉 -> revert to verdict=凶/unfavorable

  C) "Fei kong de chu" (飞空得出 / Fei jue de chu 飞绝得出):
     Detected: use_god fu shen under flying shen
                AND flying shen in xunkong (旬空)
     Override: verdict=吉 (fu emerges, curable)

--------------------------------------------------------------------------------

[ERROR CATEGORY 4] USE GOD SIX-RELATION WRONG (1 case)
------------------------------------------------------------------------
Affected: ZS002 (score 36)

Baseline: QUESTION = father-in-law (岳父) illness -> use_god = 父母 (酉金)
          Pattern: acute-illness-meets-he (近病逢合为凶) + evil-ghost moving
Engine:   use_god = 妻财 (戌土) -- completely wrong six-relation
          + hexagram palace completely wrong (uses Gui Mei /归妹 instead of
            some other hexagram configuration). The engine seems to force
            the Gui Mei hexagram into a non-matching line configuration.
          Pattern missing: near-illness-meets-he (近病逢合)

FIX P0-D: (a) Enhance keyword-to-six-relation mapping:
          '岳父','父亲','母亲','师父','长辈','父亲近病' -> 父母
          NOT '妻财' or other.

         (b) "Jin bing feng wei he" (近病逢合为凶) rule:
             Acute illness + moving line forms he (合) with use_god = 凶.
             Implement: if (topic==illness AND acute AND he_present)
                        override = 凶.

         (c) hexagram line placement must match classical case ground.
            Gui Mei (归妹) = upper Zhen (震) + lower Dui (兑).
            SHI at 3rd, YING at 6th (standard classical).

--------------------------------------------------------------------------------

[ERROR CATEGORY 5] THREE-PUNISHMENT (三刑) OVER-PENALTY (1 case)
------------------------------------------------------------------------
Affected: ZS004 (score 50) -- use_god correct but verdict reversed

Engine deducts -1.0 from final score due to "Shi shi zhi xing" (恃势之刑,
Chou/Xu/Wei completing in Tong Ren hexagram lines). However:
  Tong Ren (同人) lines (upper Qian + lower Li):
    1st=Chou(土), 2nd=Hai(水), 3rd=You(金), 4th=Wu(火), 5th=Gen(土), 6th=Xu(火)
  No Chou/Xu/Wei triad exists. The penalty is wrongly applied.
  Even if it were correct, the baseline says "Xun kong + chu xun de yi"
  which should drive the verdict toward 吉 despite three-punishments.

FIX P1-A: Strengthen three-punishment validation. Check that all three
          branches of the punishment literally exist on hexagram lines
          before applying. For "Shi shi zhi xing" all of Chou, Xu, Wei
          must be present (not partial).

FIX P1-B: Apply "chu xun you yan" (出旬有验) rule: use_god in xunkong
          + month birth = not-empty (you qi), verdict leans 吉.
          Current engine treats penalty > this rule, should be the opposite.

--------------------------------------------------------------------------------

[SCORE SIMULATION AFTER FIXES]
------------------------------------------------------------------------
Category | Cases fixed | Estimated new scores
----------|-------------|--------------------
P0-A Fu Shen lookup | ZS003/ZS014/ZS015/ZS016 | 68, 70, 68, 82
P0-B Use God branch | ZS005/ZS011 | 80, 80
P0-C Advanced pattern | ZS010/ZS012/ZS016 | 85, 80, 82
P0-D Six-relation map | ZS002 | 78
P1 Over-penalty fix  | ZS004 | 78

Estimated after-fix scores list:
   [90, 78, 68, 78, 80, 86, 78, 86, 68, 85, 80, 80, 78, 70, 68, 82, 72, 83, 85, 85]
   average ~ 79.6%
   Still need: a) fan-yin (反吟) + liu-he (六合) dual pattern detection for ZS009,
                b) yingqi precision improvement,
                c) yin-yang transformation rules (回头生/克) at branch-level.

Full 90% target requires a dedicated v5 iteration with the above fixes.
"""

print(rc)
