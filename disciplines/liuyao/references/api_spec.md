# 六爻 MCP JSON-RPC API Specification

**Version**: 1.0.0
**Protocol**: JSON-RPC 2.0 over stdio
**Last Updated**: 2025-07-28

---

## Table of Contents

1. [Overview](#1-overview)
2 [Transport Protocol](#2-transport-protocol)
3. [JSON Schema: Full Response](#3-json-schema-full-response)
4. [API Methods](#4-api-methods)
5. [Error Code Table](#5-error-code-table)
6. [Usage Examples](#6-usage-examples)
7. [Version Compatibility](#7-version-compatibility)

---

## 1. Overview

The Liu Yao MCP Server exposes the complete Liu Yao (Six Lines of Hexagram) divination engine via JSON-RPC 2.0. It supports four hexagram generation methods, full NaJia (hexagram assembly) with Six Relations / Six Spirits / Empty Death analysis, a five-step thinking chain for systematic judgment retrieval, and classical quote pattern matching.

### Capability Summary

| Capability | Method |
|-----------|--------|
| Full divination + structured analysis | `liuyao.divinate` |
| Quick reading (verdict + reasoning only) | `liuyao.quick_reading` |
| Hexagram validation against classical rules | `liuyao.validate_hexagram` |
| Classical quote pattern search | `liuyao.get_classical_quotes` |
| Method listing (introspection) | `liuyao.list_methods` |

---

## 2. Transport Protocol

**JSON-RPC 2.0 over stdio.** One JSON request per line on stdin; one JSON response per line on stdout. Each line MUST end with `\n`. The server does not write anything to stderr in normal operation (errors are encoded in JSON-RPC error objects).

### Request Envelope

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "liuyao.divinate",
  "params": { "question": "测投资", "method": "coin" }
}
```

### Success Response Envelope

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": { ... }
}
```

### Error Response Envelope

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "缺少必填参数: question"
  }
}
```

### Notifications (no-id requests)

If `"id"` is `null` or absent, the server treats the message as a notification and returns no response.

---

## 3. JSON Schema: Full Response

### 3.1 Top-Level `liuyao.divinate` Response

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LiuYaoDivinationResult",
  "description": "Complete divination result from liuyao.divinate",
  "type": "object",
  "required": [
    "question",
    "divination_time",
    "method",
    "empty_branches",
    "original_hexagram",
    "analysis_hints"
  ],
  "properties": {
    "question": {
      "type": "string",
      "description": "The question posed by the querent",
      "example": "测投资"
    },
    "divination_time": {
      "$ref": "#/definitions/DivinationTime"
    },
    "method": {
      "type": "string",
      "description": "Hexagram generation method used",
      "enum": ["铜钱摇卦", "时间起卦", "数字起卦", "手动指定"],
      "example": "铜钱摇卦"
    },
    "empty_branches": {
      "type": "array",
      "description": "Empty/void earthly branches for the day's Xun (旬空)",
      "items": { "type": "string", "pattern": "^(子|丑|寅|卯|辰|巳|午|未|申|酉|戌|亥)$" },
      "example": ["戌", "亥"]
    },
    "original_hexagram": {
      "$ref": "#/definitions/Hexagram"
    },
    "changed_hexagram": {
      "oneOf": [
        { "$ref": "#/definitions/ChangedHexagram" },
        { "type": "null" }
      ],
      "description": "Null when there are no moving lines"
    },
    "analysis_hints": {
      "$ref": "#/definitions/AnalysisHints"
    },
    "thinking_chain": {
      "oneOf": [
        { "$ref": "#/definitions/ThinkingChain" },
        { "type": "object", "additionalProperties": false }
      ],
      "description": "Five-step analytical chain; empty object when thinking_chain module is unavailable"
    }
  },
  "definitions": {
    "DivinationTime": {
      "type": "object",
      "required": ["datetime", "year_stem_branch", "month_stem_branch", "day_stem_branch", "hour_stem_branch"],
      "properties": {
        "datetime": {
          "type": "string",
          "description": "Local date-time of divination",
          "example": "2025-07-28 14:00"
        },
        "year_stem_branch": {
          "type": "array",
          "description": "Year pillar as [stem, branch]",
          "items": { "type": "string" },
          "example": ["乙", "巳"]
        },
        "month_stem_branch": {
          "type": "array",
          "description": "Month pillar as [stem, branch]",
          "items": { "type": "string" },
          "example": ["癸", "未"]
        },
        "day_stem_branch": {
          "type": "array",
          "description": "Day pillar as [stem, branch]",
          "items": { "type": "string" },
          "example": ["丙", "寅"]
        },
        "hour_stem_branch": {
          "type": "array",
          "description": "Hour pillar as [stem, branch]",
          "items": { "type": "string" },
          "example": ["乙", "未"]
        }
      }
    },
    "Hexagram": {
      "type": "object",
      "required": ["name", "sequence", "upper_trigram", "lower_trigram", "palace", "palace_element", "generation", "judgment", "yao_lines"],
      "properties": {
        "name": {
          "type": "string",
          "description": "Hexagram name (周易六十四卦名)",
          "example": "大有"
        },
        "sequence": {
          "type": "integer",
          "description": "Sequence number in the I Ching (1-64)",
          "minimum": 1,
          "maximum": 64,
          "example": 14
        },
        "upper_trigram": {
          "type": "string",
          "description": "Upper trigram name",
          "enum": ["乾", "坤", "震", "巽", "坎", "离", "艮", "兑"]
        },
        "lower_trigram": {
          "type": "string",
          "description": "Lower trigram name",
          "enum": ["乾", "坤", "震", "巽", "坎", "离", "艮", "兑"]
        },
        "palace": {
          "type": "string",
          "description": "Eight Palace (八宫) attribution",
          "example": "乾宫"
        },
        "palace_element": {
          "type": "string",
          "description": "Five-element nature of the palace",
          "enum": ["金", "木", "水", "火", "土"]
        },
        "generation": {
          "type": "string",
          "description": "Generation within the palace (本宫/一世/二世/三世/四世/五世/游魂/归魂)",
          "example": "本宫"
        },
        "judgment": {
          "type": "string",
          "description": "Classical judgment text (卦辞)",
          "example": "大有：元亨。"
        },
        "yao_lines": {
          "type": "array",
          "description": "Six lines from bottom (初爻, position 1) to top (上爻, position 6)",
          "minItems": 6,
          "maxItems": 6,
          "items": { "$ref": "#/definitions/YaoLine" }
        }
      }
    },
    "YaoLine": {
      "type": "object",
      "required": ["position", "name", "nature", "symbol", "heavenly_stem", "earthly_branch", "six_relation", "six_spirit", "is_moving", "is_world", "is_response", "is_empty", "line_text"],
      "properties": {
        "position": {
          "type": "integer",
          "description": "Line position: 1=初爻(bottom) through 6=上爻(top)",
          "minimum": 1,
          "maximum": 6
        },
        "name": {
          "type": "string",
          "description": "Classical line designation (e.g. 初九, 六二, 上六)",
          "example": "九三"
        },
        "nature": {
          "type": "string",
          "enum": ["yang", "yin"],
          "description": "Yin or yang nature of the line"
        },
        "symbol": {
          "type": "string",
          "description": "Visual representation of the line",
          "example": "▅▅▅▅▅"
        },
        "heavenly_stem": {
          "type": "string",
          "description": "NaJia heavenly stem assigned to this line",
          "enum": ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        },
        "earthly_branch": {
          "type": "string",
          "description": "NaJia earthly branch assigned to this line",
          "enum": ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        },
        "six_relation": {
          "type": "string",
          "description": "Six Relations (六亲) classification",
          "enum": ["父母", "官鬼", "子孙", "妻财", "兄弟"]
        },
        "six_spirit": {
          "type": "string",
          "description": "Six Spirits (六神) assignment based on day stem",
          "enum": ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
        },
        "is_moving": {
          "type": "boolean",
          "description": "Whether this line is moving (6=老阴 or 9=老阳)"
        },
        "is_world": {
          "type": "boolean",
          "description": "Whether this line holds the World (世) position"
        },
        "is_response": {
          "type": "boolean",
          "description": "Whether this line holds the Response (应) position"
        },
        "is_empty": {
          "type": "boolean",
          "description": "Whether this line's branch falls in the Xun empty set (旬空)"
        },
        "line_text": {
          "type": "string",
          "description": "Classical line text (爻辞) if available in the embedded corpus",
          "example": "公用亨于天子，小人弗克。"
        }
      }
    },
    "ChangedHexagram": {
      "type": "object",
      "required": ["name", "judgment", "changed_lines"],
      "properties": {
        "name": {
          "type": "string",
          "description": "Name of the changed hexagram (after moving lines flip)",
          "example": "乾"
        },
        "judgment": {
          "type": "string",
          "description": "Judgment text of the changed hexagram"
        },
        "changed_lines": {
          "type": "array",
          "description": "Positions of lines that moved (1=初爻 through 6=上爻)",
          "items": { "type": "integer", "minimum": 1, "maximum": 6 },
          "example": [3]
        }
      }
    },
    "AnalysisHints": {
      "type": "object",
      "required": ["possible_use_gods"],
      "properties": {
        "possible_use_gods": {
          "type": "array",
          "description": "Suggested Use God categories based on keyword analysis of the question",
          "items": { "type": "string" },
          "example": ["财运类：取妻财爻为用神"]
        }
      }
    },
    "ThinkingChain": {
      "type": "object",
      "required": ["step1_situational_reading", "step2_use_god_identification", "step3_strength_analysis", "step4_change_analysis", "step5_synthesis"],
      "properties": {
        "step1_situational_reading": {
          "type": "object",
          "properties": {
            "description": { "type": "string" },
            "hexagram_essence": { "type": "string" },
            "moving_summary": { "type": "string" }
          }
        },
        "step2_use_god_identification": {
          "type": "object",
          "properties": {
            "use_god_category": { "type": "string" },
            "use_god_element": { "type": "string" },
            "actual_line": { "type": ["integer", "null"] },
            "rationale": { "type": "string" }
          }
        },
        "step3_strength_analysis": {
          "type": "object",
          "properties": {
            "strength_level": { "type": "string" },
            "description": { "type": "string" },
            "monthly_influence": { "type": "string" },
            "daily_influence": { "type": "string" }
          }
        },
        "step4_change_analysis": {
          "type": "object",
          "properties": {
            "net_effect_description": { "type": "string" },
            "change_direction": { "type": "string" }
          }
        },
        "step5_synthesis": {
          "type": "object",
          "properties": {
            "verdict": { "type": "string", "description": "Final judgment e.g. '大吉', '吉', '平', '凶', '大凶'" },
            "final_score": { "type": "number", "description": "Numerical score (range typically -1.0 to 1.0)", "minimum": -1.0, "maximum": 1.0 },
            "confidence": { "type": "string" },
            "classical_quotes": {
              "type": "array",
              "items": { "type": "string" }
            },
            "advice": { "type": "string" }
          }
        }
      }
    }
  }
}
```

### 3.2 `liuyao.quick_reading` Response Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LiuYaoQuickReading",
  "type": "object",
  "required": ["verdict", "reasoning", "score", "hexagram"],
  "properties": {
    "verdict": { "type": "string", "example": "吉" },
    "reasoning": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Human-readable reasoning fragments from the thinking chain"
    },
    "score": { "type": "number", "example": 0.65 },
    "confidence": { "type": "string", "example": "中" },
    "hexagram": { "type": "string", "example": "大有" },
    "hexagram_judgment": { "type": "string" },
    "upper_trigram": { "type": "string" },
    "lower_trigram": { "type": "string" },
    "palace": { "type": "string" },
    "changed_hexagram": { "type": "string" },
    "changed_lines": {
      "type": "array",
      "items": { "type": "integer" }
    },
    "use_god": { "type": "string" },
    "use_god_element": { "type": "string" },
    "classical_quotes": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

### 3.3 `liuyao.validate_hexagram` Response Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LiuYaoValidationResult",
  "type": "object",
  "required": ["valid", "errors", "warnings"],
  "properties": {
    "valid": { "type": "boolean" },
    "errors": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Structural violations (wrong value, unrecognizable trigram etc.)"
    },
    "warnings": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Classical warnings (no moving lines, too many moving lines)"
    },
    "upper_trigram": { "type": "string" },
    "lower_trigram": { "type": "string" },
    "hexagram_name": { "type": "string" },
    "hexagram_sequence": { "type": ["integer", "null"] },
    "judgment": { "type": "string" },
    "moving_yao_positions": {
      "type": "array",
      "items": { "type": "integer" }
    }
  }
}
```

### 3.4 `liuyao.get_classical_quotes` Response Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LiuYaoClassicalQuotes",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["pattern", "source", "quote"],
    "properties": {
      "pattern": { "type": "string", "example": "六合卦" },
      "source": { "type": "string", "example": "《卜筮正宗》" },
      "quote": { "type": "string", "example": "六合卦者，买卖交通，和合纳财，百事皆吉。" }
    }
  }
}
```

---

## 4. API Methods

### 4.1 `liuyao.divinate`

Complete hexagram assembly + structured judgment analysis.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `question` | `string` | Yes | -- | The querent's question |
| `method` | `string` | No | `"coin"` | Generation method: `coin` / `time` / `number` / `manual` |
| `time` | `string` | No | current time | Fixed time `"YYYY-MM-DD HH:MM"` |
| `seed` | `integer` | No | random | RNG seed (coin method only) |
| `longitude` | `float` | No | unset | Longitude for true solar time correction |
| `numbers` | `[int, int, int]` | No | -- | Three integers for number-based generation |
| `yao` | `[int × 6]` | No | -- | Six line values (6/7/8/9 each) for manual mode |

**Returns**: `LiuYaoDivinationResult` (Section 3.1)

---

### 4.2 `liuyao.quick_reading`

Simplified verdict + reasoning chain. Always lighter than `liuyao.divinate`.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `question` | `string` | Yes | -- | The querent's question |
| `method` | `string` | No | `"coin"` | Same as divinate |
| `time` | `string` | No | current time | Same as divinate |
| `seed` | `integer` | No | random | Same as divinate |
| `numbers` | `[int, int, int]` | No | -- | Same as divinate |

**Returns**: `LiuYaoQuickReading` (Section 3.2)

---

### 4.3 `liuyao.validate_hexagram`

Validates a six-line arrangement against classical rules.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `yao` | `[int × 6]` | Yes | -- | Six line values, each must be 6, 7, 8, or 9 |

**Returns**: `LiuYaoValidationResult` (Section 3.3)

---

### 4.4 `liuyao.get_classical_quotes`

Retrieves classical text quotes matching a pattern name.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `pattern` | `string` | Yes | -- | Pattern name e.g. `"六合卦"`, `"游魂"`, `"用神旺"` |

**Returns**: `LiuYaoClassicalQuotes` (Section 3.4)

---

### 4.5 `liuyao.list_methods`

Introspection method. Returns all available methods and their descriptions.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| *(none)* | -- | -- | -- | Returns method catalog |

```json
{
  "result": {
    "methods": {
      "liuyao.divinate": "完整排盘+断卦（支持 coin/time/number/manual 四种起卦方式）",
      "liuyao.quick_reading": "简化版断卦，仅返回判语+推理链",
      "liuyao.validate_hexagram": "校验六爻排列 [6,7,8,9] 是否符合古典规则",
      "liuyao.get_classical_quotes": "按格局名称检索经典引文",
      "liuyao.list_methods": "（内建）列出所有可用方法的帮助信息"
    }
  }
}
```

---

## 5. Error Code Table

All codes follow JSON-RPC 2.0 standard extensions.

| Code | Constant | Meaning | Typical Cause |
|------|----------|---------|---------------|
| `-32700` | `ERROR_PARSE_ERROR` | Invalid JSON received | Malformed request body |
| `-32600` | `ERROR_INVALID_REQUEST` | Invalid JSON-RPC structure | Missing `jsonrpc: "2.0"` or missing `method` field |
| `-32601` | `ERROR_METHOD_NOT_FOUND` | Unknown method name | Typo in method; check `data.available_methods` |
| `-32602` | `ERROR_INVALID_PARAMS` | Invalid parameters | Missing `question`, invalid `yao` values, wrong `method` string |
| `-32603` | `ERROR_INTERNAL_ERROR` | Server internal error | Unexpected exception during processing |
| `-32000` | `ERROR_SERVER_ERROR` | Server-specific error | Reserved for future use |

### Error Response Shape

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "数字起卦需要 numbers 参数（3个整数）"
  }
}
```

For `-32601`, the error object includes a `data` field with available method names:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found: liuyao.unknown",
    "data": {
      "available_methods": [
        "liuyao.divinate",
        "liuyao.quick_reading",
        "liuyao.validate_hexagram",
        "liuyao.get_classical_quotes",
        "liuyao.list_methods"
      ]
    }
  }
}
```

---

## 6. Usage Examples

### 6.1 MCP over stdio (bash one-liner)

```bash
# Start the server and send a request via stdin
echo '{"jsonrpc":"2.0","id":1,"method":"liuyao.divinate","params":{"question":"测投资","method":"coin"}}' | python mcp_server.py

# Quick reading
echo '{"jsonrpc":"2.0","id":2,"method":"liuyao.quick_reading","params":{"question":"测感情"}}' | python mcp_server.py

# Validate hexagram
echo '{"jsonrpc":"2.0","id":3,"method":"liuyao.validate_hexagram","params":{"yao":[7,8,9,7,6,8]}}' | python mcp_server.py

# Get classical quotes
echo '{"jsonrpc":"2.0","id":4,"method":"liuyao.get_classical_quotes","params":{"pattern":"六合卦"}}' | python mcp_server.py
```

### 6.2 `liuyao.divinate` with fixed seed (reproducible)

```bash
echo '{"jsonrpc":"2.0","id":5,"method":"liuyao.divinate","params":{"question":"测出行","method":"coin","seed":42}}' | python mcp_server.py
```

### 6.3 Time-based hexagram

```bash
echo '{"jsonrpc":"2.0","id":6,"method":"liuyao.divinate","params":{"question":"测考试","method":"time","time":"2025-08-15 09:00"}}' | python mcp_server.py
```

### 6.4 Number-based hexagram

```bash
echo '{"jsonrpc":"2.0","id":7,"method":"liuyao.divinate","params":{"question":"测事业","method":"number","numbers":[3,6,9]}}' | python mcp_server.py
```

### 6.5 Manual hexagram

```bash
echo '{"jsonrpc":"2.0","id":8,"method":"liuyao.divinate","params":{"question":"测家宅","method":"manual","yao":[7,8,9,7,6,8]}}' | python mcp_server.py
```

### 6.6 Python direct API (no JSON-RPC)

```python
import sys
sys.path.insert(0, "scripts/")

from mcp_server import _method_divinate, _method_quick_reading, _method_validate_hexagram, _method_get_classical_quotes

# Full divination
result = _method_divinate({
    "question": "测投资",
    "method": "coin",
    "seed": 42,
})
print(result["original_hexagram"]["name"])   # e.g. "大有"
print(result["thinking_chain"]["step5_synthesis"]["verdict"])

# Quick reading
quick = _method_quick_reading({"question": "测感情"})
print(quick["verdict"])
print(quick["score"])

# Validate
v = _method_validate_hexagram({"yao": [7, 8, 9, 7, 6, 8]})
print(v["valid"], v.get("hexagram_name"))

# Classical quotes
quotes = _method_get_classical_quotes({"pattern": "回头克"})
for q in quotes:
    print(f"[{q['source']}] {q['quote']}")
```

### 6.7 Python using engine directly

```python
import sys
sys.path.insert(0, "scripts/")

from liuyao_engine import coin_toss, build_hexagram_result

yao = coin_toss()
result = build_hexagram_result(yao, "测投资", "铜钱摇卦", 2025, 7, 28, 14)
print(result["original_hexagram"]["name"])
print(result["divination_time"]["day_stem_branch"])
```

### 6.8 Validation error example

Request:
```json
{"jsonrpc":"2.0,"id":9,"method":"liuyao.validate_hexagram","params":{"yao":[5,7,8,9,7,6]}}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "result": {
    "valid": false,
    "errors": ["第1爻值 5 不合法（必须为6/7/8/9）"],
    "warnings": [],
    "upper_trigram": "乾",
    "lower_trigram": "巽"
  }
}
```

---

## 7. Version Compatibility

### Version Matrix

| mcp_server.py | liuyao_engine.py | thinking_chain.py | Compatible? |
|---------------|------------------|-------------------|-------------|
| 1.0.0         | any with `build_hexagram_result()`, `coin_toss()`, `time_based_hexagram()`, `number_based_hexagram()` | Optional (graceful fallback to empty `thinking_chain: {}`) | Yes |

### Backward-Compatibility Notes

1. **Thinking chain is optional.** If `thinking_chain.py` is not importable, the server returns `thinking_chain: {}` (empty object) rather than erroring. Clients MUST handle this.

2. **Classical analysis is optional.** If `classical_analysis.py` is missing, divination proceeds without classical enhancement.

3. **Event logging is optional.** If `event_logger.py` is missing or fails silently, divination still completes. No error is raised.

4. **Engine imports are required.** `liuyao_engine.py` must export: `coin_toss`, `time_based_hexagram`, `number_based_hexagram`, `build_hexagram_result`, `BAGUA`, `TRIGRAM_LOOKUP`, `HEXAGRAM_LOOKUP`.

5. **New fields may be added.** Future minor versions MAY add new optional fields to responses. Clients SHOULD be tolerant of unexpected extra fields per JSON Schema `additionalProperties` defaults.

6. **Field removal is a breaking change.** Removing a documented field requires a major version bump (2.0.0+).

### Minimum Python Version

Python 3.10+ (due to `match` / `X | Y` union syntax and `from __future__ import annotations` usage in chain modules). Python 3.12 is the primary test target.
