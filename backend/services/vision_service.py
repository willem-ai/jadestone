"""
Vision service: 通义千问 VL Max 诊断性特征识别.
Sends photos to Qwen VL Max and gets back a diagnostic feature report.
"""

import base64
import json
import mimetypes
from pathlib import Path
from typing import List, Optional

import httpx

from config import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    VISION_MODEL,
    VISION_MODEL_FALLBACK,
    DEMO_MODE,
)


VISION_PROMPT_PATH = Path(__file__).parent.parent / "data" / "vision_prompt.md"


def _load_vision_prompt() -> str:
    if VISION_PROMPT_PATH.exists():
        return VISION_PROMPT_PATH.read_text(encoding="utf-8")
    return "你是翡翠原石的诊断性特征观察员。请仔细观察照片中的翡翠原石，描述其皮壳特征。"


def _encode_image(image_path: str) -> str:
    """Encode image file as base64 data URL."""
    mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def _build_image_content(image_paths: List[str]) -> List[dict]:
    """Build the content array with text + images for Qwen VL API."""
    content = [{"type": "text", "text": "请仔细观察以下翡翠原石照片，按照你的System Prompt要求输出诊断性特征观察报告。"}]
    for path in image_paths:
        data_url = _encode_image(path)
        content.append({"type": "image_url", "image_url": {"url": data_url}})
    return content


async def analyze_images(
    image_paths: List[str],
    model: Optional[str] = None,
) -> str:
    """
    Send images to Qwen VL Max and get diagnostic feature report.

    Returns:
        str: Structured diagnostic feature observation report in Chinese.
    """
    if DEMO_MODE:
        return _demo_report(image_paths)

    vision_prompt = _load_vision_prompt()
    models_to_try = [model] if model else [VISION_MODEL, VISION_MODEL_FALLBACK]
    models_to_try = [m for m in models_to_try if m]

    last_error = None
    for model_name in models_to_try:
        try:
            return await _call_qwen_vl(vision_prompt, image_paths, model_name)
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"All vision models failed. Last error: {last_error}")


async def _call_qwen_vl(system_prompt: str, image_paths: List[str], model: str) -> str:
    """Call Qwen VL API via DashScope OpenAI-compatible endpoint."""
    if not DASHSCOPE_API_KEY:
        raise ValueError("DASHSCOPE_API_KEY is not set")

    content = _build_image_content(image_paths)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{DASHSCOPE_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
                "temperature": 0.1,
                "max_tokens": 4096,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


def _demo_report(image_paths: List[str]) -> str:
    """Generate a realistic demo diagnostic report when no API key is configured."""
    photo_count = len(image_paths)
    return f"""【照片质量评估】
- 共收到{photo_count}张照片
- 自然光照: 清晰, 光线充足 ★★★★☆
- 打灯照: 清晰, 打灯位置可见 ★★★★☆
- 微距照: 清晰, 可分辨皮壳纹理 ★★★★☆

【砂粒粗细度】
- 砂粒粗细: 细密 ★★★★☆
- 判据: 微距照片显示皮壳表面颗粒均匀细腻, 肉眼难以分辨单粒, 触感应如面粉
- 诊断含义: 细密砂粒通常指示内部晶体结构致密, 种老的可靠信号

【打灯反应】
- 透光深度: >3cm ★★★★☆
- 透光颜色: 偏白偏绿, 分布较均匀
- 光圈大小和形态: 光圈大而均匀, 边界清晰
- 诊断含义: 透光深+光圈均匀=内部纯净度较高, 种水大概率在冰种区间

【裂纹观察】
- 可见裂纹: 1条 ★★★★☆
- 裂纹1: 位于左侧, 斜向45°走向, 长约3cm, 肉眼可见已开口, 宽度约0.5mm
- 深度判断: 从多角度观察, 裂纹在侧面照片中延续可见, 可能已深入内部
- 风险分级: 高 — 开口裂纹深入内部概率约60-70%

【松花】
- 分布形态: 带状分布, 连续性好 ★★★★☆
- 颜色浓度: 深绿
- 密度: 中等偏密, 覆盖正面约15%面积
- 诊断含义: 带状连续深绿松花→内部有绿概率较高, 约70%

【蟒带】
- 宽窄: 宽蟒, 约2.5cm ★★★☆☆
- 清晰度: 边界较清晰
- 走向: 水平走向, 位于石头中部
- 诊断含义: 宽蟒较清晰→蟒下可能有色带

【癣】
- 未发现明显癣迹 ★★★★☆

【皮壳类型】
- 类型: 白沙皮 ★★★★☆
- 常见场口: 木那/莫西沙
- 该类型先验: 白沙皮出冰种的概率相对较高

【处理痕迹】
- 酸洗纹: 未发现 ★★★★☆
- 染色痕迹: 未发现 ★★★★☆
- 注胶痕迹: 未发现 ★★★★☆
- 皮壳做旧: 自然氧化, 色泽过渡自然 ★★★★☆
- 综合: 处理风险低

【形状与体量】
- 整体形状: 不规则椭圆形
- 大致尺寸: 约12×8×6cm (基于照片中手部参照估算, ±25%误差)
- 表面平整度: 较平整, 有轻微凹凸"""
