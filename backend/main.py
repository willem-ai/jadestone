"""
JadeStone MVP — FastAPI Backend.

POST /api/evaluate  — Accepts images, returns probabilistic assessment.
GET  /api/cases     — List all cases.
POST /api/cases     — Add a new case (with cut result).
GET  /health        — Health check.
"""

import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import (
    UPLOAD_DIR,
    MAX_IMAGES_NATURAL,
    MAX_IMAGES_LAMP,
    MAX_IMAGES_MACRO,
    MAX_FILE_SIZE_MB,
)
from services.vision_service import analyze_images
from services.clip_embedding import compute_embedding
from services.case_store import case_store
from services.deepseek_agent import evaluate as deepseek_evaluate
from services.model_fallback import fallback_state

app = FastAPI(
    title="JadeStone MVP API",
    version="4.0.0",
    description="翡翠原石AI评估 — 基于皮壳的概率性内部推断",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def _save_upload(file: UploadFile, subdir: str) -> Path:
    """Save an uploaded file to a subdirectory under UPLOAD_DIR."""
    if file.size and file.size > MAX_FILE_BYTES:
        raise HTTPException(400, f"File {file.filename} exceeds {MAX_FILE_SIZE_MB}MB limit")

    dest_dir = UPLOAD_DIR / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix if file.filename else ".jpg"
    fname = f"{uuid.uuid4().hex}{ext}"
    dest = dest_dir / fname

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return dest


def _validate_images(files: list[UploadFile], max_count: int, category: str) -> list[UploadFile]:
    """Validate and filter uploaded files."""
    if not files:
        return []
    valid = []
    for f in files[:max_count]:
        if f.filename and f.size and f.size > 0:
            valid.append(f)
    return valid


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "demo_mode": fallback_state.is_demo_mode,
        "vision_tier": fallback_state.vision_tier.value,
        "reasoning_tier": fallback_state.reasoning_tier.value,
        "case_count": case_store.count(),
    }


@app.post("/api/evaluate")
async def evaluate(
    images_natural: list[UploadFile] = File(..., description="自然光照片, 1-6张"),
    images_lamp: list[UploadFile] = File(..., description="强光打灯照片, 1-4张"),
    images_macro: list[UploadFile] = File(default=[], description="微距皮壳照片, 1-2张 (可选)"),
    weight_g: Optional[float] = Form(None, description="石头重量(克)"),
    mine: Optional[str] = Form(None, description="场口"),
    ask_price: Optional[float] = Form(None, description="卖家报价(元)"),
):
    """
    Evaluate a jade stone from photos.

    Flow:
    1. Qwen VL Max → diagnostic feature report
    2. Chinese-CLIP → similar case retrieval (parallel with step 1)
    3. DeepSeek V4 Pro → probabilistic assessment JSON
    """
    # Validate and save images
    natural = _validate_images(images_natural, MAX_IMAGES_NATURAL, "natural")
    lamp = _validate_images(images_lamp, MAX_IMAGES_LAMP, "lamp")
    macro = _validate_images(images_macro, MAX_IMAGES_MACRO, "macro")

    if not natural and not lamp:
        raise HTTPException(400, "至少需要提供自然光照片或打灯照片")

    saved_paths: list[str] = []
    try:
        for f in natural:
            saved_paths.append(str(_save_upload(f, "natural")))
        for f in lamp:
            saved_paths.append(str(_save_upload(f, "lamp")))
        for f in macro:
            saved_paths.append(str(_save_upload(f, "macro")))

        # Step 1 & 2: Vision analysis + CLIP retrieval (concurrent conceptually,
        # but vision first gives the report; CLIP runs independently)
        import asyncio

        async def run_vision():
            return await analyze_images(saved_paths)

        async def run_search():
            query_emb = compute_embedding(saved_paths)
            similar, stats = case_store.search(query_emb)
            return similar, stats

        # Run vision and CLIP search concurrently
        vision_task = asyncio.create_task(run_vision())
        search_task = asyncio.create_task(run_search())

        vision_report = await vision_task
        similar_cases, case_stats = await search_task

        # Step 3: DeepSeek V4 Pro reasoning
        assessment = await deepseek_evaluate(
            vision_report=vision_report,
            similar_cases=similar_cases,
            case_stats=case_stats,
            weight_g=weight_g,
            mine=mine,
            ask_price=ask_price,
        )

        cost_estimate = _estimate_cost(vision_report)

        return {
            "mode": "LOW_INFO",
            "demo_mode": fallback_state.is_demo_mode,
            "vision_report": vision_report,
            "assessment": assessment.get("assessment", assessment),
            "similar_cases": similar_cases,
            "case_statistics": case_stats,
            "cost_breakdown": cost_estimate,
        }

    except Exception as e:
        raise HTTPException(500, f"Evaluation failed: {e}")


def _estimate_cost(vision_report: str) -> dict:
    """Rough cost estimate based on output length."""
    vision_tokens = len(vision_report) // 2  # rough estimate
    reasoning_tokens = 8192  # max tokens configured
    thinking_tokens = 4096

    vision_cost = round(vision_tokens * 0.00002, 4)  # ~¥0.02/1K tokens
    reasoning_cost = round((reasoning_tokens + thinking_tokens) * 0.000008, 4)

    return {
        "vision_api": vision_cost,
        "deepseek_api": reasoning_cost,
        "clip_embedding": 0.00,
        "total": round(vision_cost + reasoning_cost, 4),
        "currency": "CNY",
        "note": "估算值, 实际以API账单为准",
    }


@app.get("/api/cases")
async def list_cases():
    """List all cases (without full details)."""
    return {
        "total": case_store.count(),
        "cases": [
            {
                "id": c["id"],
                "skin_type": c.get("skin_type"),
                "final_result": c.get("final_result"),
                "output_water": c.get("output_water"),
                "output_color": c.get("output_color"),
            }
            for c in case_store.cases
        ],
    }


@app.post("/api/cases")
async def add_case(case: dict):
    """Add a new case with cut result."""
    added = case_store.add(case)
    return {"status": "ok", "case": added}


@app.delete("/api/cases/{case_id}")
async def delete_case(case_id: int):
    """Delete a case."""
    if case_store.delete(case_id):
        return {"status": "ok"}
    raise HTTPException(404, f"Case {case_id} not found")


if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
