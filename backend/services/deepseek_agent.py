"""
DeepSeek Agent: DeepSeek V4 Pro 概率性推理.
Takes diagnostic report + similar cases + user inputs → structured JSON assessment.
"""

import json
import re
from pathlib import Path
from typing import Optional

import httpx

from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    REASONING_MODEL,
    THINKING_BUDGET,
    MAX_TOKENS,
    DEMO_MODE,
)


AGENT_PROMPT_PATH = Path(__file__).parent.parent / "data" / "agent_prompt.md"
DOMAIN_KNOWLEDGE_PATH = Path(__file__).parent.parent / "data" / "domain_knowledge.txt"


def _load_agent_prompt() -> str:
    prompt = ""
    if AGENT_PROMPT_PATH.exists():
        prompt += AGENT_PROMPT_PATH.read_text(encoding="utf-8")
    if DOMAIN_KNOWLEDGE_PATH.exists():
        prompt += "\n\n## 详细领域知识\n\n"
        prompt += DOMAIN_KNOWLEDGE_PATH.read_text(encoding="utf-8")
    return prompt


def _load_json_schema() -> str:
    """Return the expected JSON Schema as part of the system prompt."""
    return r"""
## 输出 JSON Schema (严格遵守)

你必须输出以下结构的 JSON。所有推断字段必须包含完整的五要素。

```json
{
  "assessment": {
    "mode": "LOW_INFO",
    "mode_note": "基于皮壳+打灯的概率性推断, 无开窗验证",
    "signal_summary": {
      "positive_signals": ["string, 每个正向信号+确定性"],
      "negative_signals": ["string, 每个负向信号+确定性"],
      "signal_consistency": "一致 | 基本一致 | 部分矛盾 | 严重矛盾",
      "consistency_detail": "解释信号之间的关系"
    },
    "overall_quality_grade": "B+ | B | B- | C+ | C | 信号过弱无法评估",
    "overall_confidence": 0.0,
    "overall_confidence_rationale": "综合置信度的计算依据",

    "water_type_inference": {
      "inferred": "string, 推断的种水类型",
      "confidence": 0.0,
      "alternative": {"糯冰": 0.0, "冰种": 0.0, "玻璃种": 0.0, "糯种": 0.0, "豆种": 0.0},
      "basis": [{"feature": "string", "diagnostic_weight": 0.0, "direction": "positive|negative"}],
      "reasoning": "推理链条",
      "counter_argument": "反例/什么情况下会错",
      "case_support": {
        "similar_cases_total": 0,
        "cases_supporting_ice": 0,
        "cases_supporting_nuobing": 0,
        "cases_supporting_glass": 0,
        "cases_cut_fail": 0,
        "representative_case": "string"
      }
    },

    "color_inference": {
      "inferred": "string",
      "confidence": 0.0,
      "alternative": {},
      "basis": [],
      "reasoning": "string",
      "counter_argument": "string",
      "case_support": {
        "similar_cases_total": 0,
        "cases_with_green": 0,
        "cases_without_green": 0,
        "representative_case": "string"
      }
    },

    "clarity_inference": {
      "inferred": "string",
      "confidence": 0.0,
      "alternative": {},
      "basis": [],
      "reasoning": "string",
      "counter_argument": "string",
      "case_support": {
        "similar_cases_total": 0,
        "cases_light_cotton": 0,
        "cases_medium_cotton": 0,
        "cases_heavy_cotton": 0
      }
    },

    "crack_analysis": {
      "visible_cracks": 0,
      "details": [{
        "id": 0,
        "location": "string",
        "direction": "string",
        "length_cm": "string",
        "width": "string",
        "depth_inference": {
          "inferred": "string",
          "confidence": 0.0,
          "basis": [],
          "counter_argument": "string",
          "case_support": "string"
        },
        "risk_level": "高|中|低",
        "value_impact": "string"
      }],
      "overall_crack_risk": "高|中高|中|中低|低",
      "note": "string"
    },

    "treatment_risk": {
      "level": "低|中|高|无法判断",
      "confidence": 0.0,
      "indicators": [],
      "counter_argument": "string"
    },

    "shape_volume": {
      "shape": "string",
      "estimated_dimensions_cm": {"length": 0, "width": 0, "height": 0},
      "estimation_method": "string",
      "estimated_weight_g": 0,
      "confidence": "string"
    },

    "case_statistics": {
      "total_similar": 0,
      "cut_up": 0,
      "cut_even": 0,
      "cut_down": 0,
      "cut_up_rate": 0.0,
      "note": "string"
    },

    "price_reference": {
      "estimated_market_range": "string",
      "basis": "string",
      "confidence": "string",
      "bargaining_recommendation": "string"
    },

    "risk_summary": {
      "overall_risk_level": "高|中高|中|中低|低",
      "top_risks": [{"risk": "string", "severity": "高|中|低", "mitigation": "string"}],
      "positive_factors": ["string"],
      "decision_aid": {
        "recommendation": "string",
        "max_suggested_bid_percent": 0,
        "rationale": "string",
        "deal_breaker": "string",
        "next_best_action": "string"
      }
    }
  }
}
```
"""


async def evaluate(
    vision_report: str,
    similar_cases: list[dict],
    case_stats: dict,
    weight_g: Optional[float] = None,
    mine: Optional[str] = None,
    ask_price: Optional[float] = None,
) -> dict:
    """
    Send vision report + case data to DeepSeek V4 Pro for probabilistic assessment.

    Returns:
        dict: Structured assessment JSON.
    """
    if DEMO_MODE:
        return _demo_assessment(vision_report, similar_cases, case_stats, weight_g, mine, ask_price)

    system_prompt = _load_agent_prompt() + "\n\n" + _load_json_schema()

    # Build user prompt
    user_parts = [
        "## 诊断性特征观察报告\n\n",
        vision_report,
        "\n\n## 相似案例\n\n",
        json.dumps(similar_cases, ensure_ascii=False, indent=2),
        "\n\n## 案例统计\n\n",
        json.dumps(case_stats, ensure_ascii=False, indent=2),
    ]

    user_inputs = []
    if weight_g:
        user_inputs.append(f"- 石头重量: {weight_g}g")
    if mine:
        user_inputs.append(f"- 场口: {mine}")
    if ask_price:
        user_inputs.append(f"- 卖家报价: ¥{ask_price}")
    if user_inputs:
        user_parts.insert(1, "## 用户提供信息\n\n" + "\n".join(user_inputs) + "\n")

    user_prompt = "".join(user_parts)

    try:
        return await _call_deepseek(system_prompt, user_prompt)
    except Exception as e:
        raise RuntimeError(f"DeepSeek API call failed: {e}")


async def _call_deepseek(system_prompt: str, user_prompt: str) -> dict:
    """Call DeepSeek V4 Pro API."""
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY is not set")

    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": REASONING_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
                "max_tokens": MAX_TOKENS,
                "extra_body": {"thinking": {"type": "enabled", "budget": THINKING_BUDGET}},
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return _extract_json(content)


def _extract_json(text: str) -> dict:
    """Extract JSON from model output, handling markdown code blocks."""
    # Try to find JSON in code blocks first
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        text = match.group(1)
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find the outermost JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start:end + 1])
        raise ValueError(f"Failed to parse JSON from response: {text[:200]}...")


def _demo_assessment(
    vision_report: str,
    similar_cases: list[dict],
    case_stats: dict,
    weight_g: Optional[float],
    mine: Optional[str],
    ask_price: Optional[float],
) -> dict:
    """Generate a demo assessment when API keys are not configured."""
    return {
        "assessment": {
            "mode": "LOW_INFO",
            "mode_note": "基于皮壳+打灯的概率性推断, 无开窗验证 [DEMO MODE]",
            "signal_summary": {
                "positive_signals": [
                    "砂粒极细密 ★★★★★",
                    "打灯透光>3cm ★★★★☆",
                    "松花带状分布, 色深绿 ★★★★☆",
                    "宽蟒>2cm, 边界清晰 ★★★☆☆",
                    "处理风险低 ★★★★☆"
                ],
                "negative_signals": [
                    "左侧开口裂纹 ★★★★☆"
                ],
                "signal_consistency": "基本一致",
                "consistency_detail": "砂粒和打灯均正向, 松花+蟒带双信号支持内部有色, 裂纹是唯一的负向信号, 信号总体一致"
            },
            "overall_quality_grade": "B+",
            "overall_confidence": 0.62,
            "overall_confidence_rationale": "两个一级正向信号强(砂细+打灯好), 松花+蟒带双信号支持有色, 被一个负向信号(开口裂)部分抵消, 综合置信度62%",
            "water_type_inference": {
                "inferred": "冰种",
                "confidence": 0.65,
                "alternative": {"玻璃种": 0.05, "冰种": 0.65, "糯冰": 0.25, "糯种": 0.05, "豆种": 0.00},
                "basis": [
                    {"feature": "砂粒极细密 ★★★★★", "diagnostic_weight": 0.30, "direction": "positive"},
                    {"feature": "打灯透光>3cm ★★★★☆", "diagnostic_weight": 0.25, "direction": "positive"},
                    {"feature": "皮壳类型: 白沙皮 (木那) → 冰种先验", "diagnostic_weight": 0.10, "direction": "positive"}
                ],
                "reasoning": "砂细→晶体结构致密→冰种特征; 打灯深透→内部纯净度较高; 木那白沙皮是冰种高发皮壳类型。三个正向信号叠加, 冰种推断置信度65%",
                "counter_argument": "无开窗=无法排除内部变种可能; 表皮细腻不代表内部通体一致; 打灯位置不同结论可能有变化; 可能仅是表皮冰感, 内部降为糯冰",
                "case_support": {
                    "similar_cases_total": 5,
                    "cases_supporting_ice": 3,
                    "cases_supporting_nuobing": 2,
                    "cases_supporting_glass": 0,
                    "cases_cut_fail": 0,
                    "representative_case": "案例#1: 木那白沙皮, 类似砂粒+透光, 切出冰种飘蓝花, 出货价¥18万"
                }
            },
            "color_inference": {
                "inferred": "飘蓝花",
                "confidence": 0.55,
                "alternative": {"飘绿花": 0.25, "满绿": 0.05, "飘蓝花": 0.55, "无色": 0.15},
                "basis": [
                    {"feature": "松花带状分布 ★★★★☆, 色深绿", "diagnostic_weight": 0.25, "direction": "positive"},
                    {"feature": "打灯透光偏白偏绿 ★★★☆☆", "diagnostic_weight": 0.15, "direction": "positive"},
                    {"feature": "宽蟒>2cm ★★★☆☆", "diagnostic_weight": 0.10, "direction": "positive"}
                ],
                "reasoning": "松花带状+色深暗示内部有绿; 蟒带暗示有色带走向; 打灯偏白偏绿支持无色底+飘绿花。松花形态更接近飘花类型(非满色型松花)",
                "counter_argument": "松花可能仅表皮; 蟒下有色是概率规则非必然; 松花带状可能纵向分布不广; 颜色浓度无法从表皮精确判断",
                "case_support": {
                    "similar_cases_total": 5,
                    "cases_with_green": 3,
                    "cases_without_green": 2,
                    "representative_case": "案例#1: 类似松花分布, 内部飘蓝花面积约40%"
                }
            },
            "clarity_inference": {
                "inferred": "微棉, 点状分布",
                "confidence": 0.45,
                "alternative": {"少棉": 0.30, "微棉点状": 0.45, "团状棉": 0.15, "大面积棉": 0.10},
                "basis": [
                    {"feature": "打灯光圈较均匀 ★★★☆☆", "diagnostic_weight": 0.20, "direction": "positive"},
                    {"feature": "砂粒细密 ★★★★★", "diagnostic_weight": 0.15, "direction": "positive"}
                ],
                "reasoning": "打灯光圈均匀=内部结构一致性较好; 砂细=晶体细腻, 棉通常不重。但棉的分布是推断中最不确定的维度",
                "counter_argument": "棉的分布和形态是内部品质中最难从表皮判断的维度; 小区域棉在打灯中不可见; 案例中类似皮壳棉的分布差异很大",
                "case_support": {
                    "similar_cases_total": 5,
                    "cases_light_cotton": 3,
                    "cases_medium_cotton": 1,
                    "cases_heavy_cotton": 1
                }
            },
            "crack_analysis": {
                "visible_cracks": 1,
                "details": [{
                    "id": 1,
                    "location": "左侧",
                    "direction": "斜向45°",
                    "length_cm": "约3",
                    "width": "肉眼可见, 已开口",
                    "depth_inference": {
                        "inferred": "可能深入内部",
                        "confidence": 0.65,
                        "basis": ["开口裂纹 ★★★★☆, 非细如发丝", "斜向45°可能沿解理面延伸"],
                        "counter_argument": "也可能是表皮裂纹, 不深入; 需要多角度照确认; 打灯观察裂纹处透光是否中断可辅助判断",
                        "case_support": "案例库中类似开口裂纹深入内部的概率约60% (案例#6: 开口裂贯穿; 案例#2: 表皮裂未深入)"
                    },
                    "risk_level": "高",
                    "value_impact": "裂纹若深入内部, 手镯出材率降低30-50%; 只能出牌子/挂件"
                }],
                "overall_crack_risk": "中高",
                "note": "无开窗=裂纹实际深度无法确认, 这是本评估最大的不确定性来源"
            },
            "treatment_risk": {
                "level": "低",
                "confidence": 0.8,
                "indicators": ["皮壳自然, 未见酸蚀纹理 ★★★★☆", "表面无异常胶状光泽 ★★★★☆", "色泽自然过渡 ★★★☆☆"],
                "counter_argument": "高级处理货可能不露痕迹; 仅靠照片识别处理货有局限; 建议结合紫外荧光灯检测"
            },
            "shape_volume": {
                "shape": "不规则椭圆形",
                "estimated_dimensions_cm": {"length": 12, "width": 8, "height": 6},
                "estimation_method": "基于照片中手部参照估算",
                "estimated_weight_g": weight_g or 1200,
                "confidence": "±25%"
            },
            "case_statistics": case_stats or {
                "total_similar": 5,
                "cut_up": 3,
                "cut_even": 1,
                "cut_down": 1,
                "cut_up_rate": 0.6,
                "note": "5个案例统计意义有限, 仅供方向性参考"
            },
            "price_reference": {
                "estimated_market_range": "¥5-15万",
                "basis": "相似皮壳+打灯的案例中, 冰种出货价¥8-18万; 但无开窗, 考虑裂纹风险折扣30%",
                "confidence": "低 (无开窗原石价格波动极大)",
                "bargaining_recommendation": "买家可利用'开口裂纹深度未知'+'无开窗'压价, 建议出价不超过¥8万"
            },
            "risk_summary": {
                "overall_risk_level": "中高",
                "top_risks": [
                    {"risk": "无开窗=所有内部推断未经直接验证", "severity": "高", "mitigation": "如可能, 建议开小窗验证; 或以无开窗料的价格策略购入"},
                    {"risk": "左侧开口裂纹可能深入内部", "severity": "高", "mitigation": "多角度拍照确认深度; 打灯看裂纹处是否阻断透光; 案例中60%深入率"},
                    {"risk": "松花可能仅停留在表皮", "severity": "中", "mitigation": "松花+蟒带双信号交叉验证, 有色概率已上调至55%; 但仍非确定"}
                ],
                "positive_factors": [
                    "砂粒极细密 — 最强正向信号, 种水高概率冰种区间",
                    "打灯透光深且均匀 — 内部纯净度较高的证据",
                    "松花+蟒带双信号 — 内部有色的交叉验证",
                    "处理风险低 — 天然A货概率高",
                    "案例库3/5切涨 — 相似案例偏乐观"
                ],
                "decision_aid": {
                    "recommendation": "谨慎考虑入手, 但需要压价",
                    "max_suggested_bid_percent": 60,
                    "rationale": "正向信号多但无开窗验证+裂纹风险; 以有开窗同品质石头的60%出价是合理赌博策略; 65%冰种概率+60%切涨率=正期望值, 但方差大",
                    "deal_breaker": "如果卖家不让打灯/不让多角度拍照 → 坚决不买",
                    "next_best_action": "如可能, 在左侧裂纹处开小窗验证深度; 或要求卖家提供裂纹处的打灯透光照"
                }
            }
        }
    }
