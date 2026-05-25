"""
Chinese-CLIP embedding service for case retrieval.
Uses Chinese-CLIP for image embedding and cosine similarity search.
Falls back to text-based similarity when CLIP model is not available.
"""

import json
import math
import random
from pathlib import Path
from typing import List, Optional

import numpy as np

from config import (
    CLIP_MODEL_NAME,
    CLIP_CACHE_DIR,
    FEATURES_FILE,
    TOP_K_CASES,
    DEMO_MODE,
)


# Lazy-loaded model and processor
_model = None
_processor = None


def _get_model_and_processor():
    """Lazy load Chinese-CLIP model. Returns (model, processor) or (None, None) on failure."""
    global _model, _processor
    if _model is not None:
        return _model, _processor
    try:
        from transformers import ChineseCLIPProcessor, ChineseCLIPModel
        import torch

        _model = ChineseCLIPModel.from_pretrained(
            CLIP_MODEL_NAME,
            cache_dir=CLIP_CACHE_DIR,
        )
        _processor = ChineseCLIPProcessor.from_pretrained(
            CLIP_MODEL_NAME,
            cache_dir=CLIP_CACHE_DIR,
        )
        _model.eval()
        return _model, _processor
    except Exception:
        return None, None


def compute_embedding(image_paths: List[str]) -> np.ndarray:
    """
    Compute Chinese-CLIP embedding for one or more images.

    When multiple images are provided, their embeddings are averaged.
    Falls back to text-based features if CLIP model is not available.
    """
    model, processor = _get_model_and_processor()

    if model is None or DEMO_MODE:
        return _fallback_embedding(image_paths)

    import torch
    from PIL import Image

    embeddings = []
    for path in image_paths:
        try:
            image = Image.open(path).convert("RGB")
            inputs = processor(images=image, return_tensors="pt")
            with torch.no_grad():
                emb = model.get_image_features(**inputs)
            embeddings.append(emb.squeeze(0).cpu().numpy())
        except Exception:
            continue

    if not embeddings:
        return _fallback_embedding(image_paths)

    avg_embedding = np.mean(embeddings, axis=0)
    # Normalize
    norm = np.linalg.norm(avg_embedding)
    if norm > 0:
        avg_embedding = avg_embedding / norm
    return avg_embedding


def _fallback_embedding(image_paths: List[str]) -> np.ndarray:
    """
    Generate a deterministic pseudo-embedding from image file characteristics.
    Only used when CLIP model is unavailable — produces consistent embeddings
    for the same set of files but has no semantic meaning.
    """
    seed = 0
    for path in sorted(image_paths):
        p = Path(path)
        if p.exists():
            stat = p.stat()
            seed ^= hash(str(p.name)) ^ hash(stat.st_size) ^ hash(int(stat.st_mtime))
    rng = random.Random(seed)
    emb = np.array([rng.random() for _ in range(768)], dtype=np.float32)
    norm = np.linalg.norm(emb)
    return emb / norm


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two normalized embeddings."""
    return float(np.dot(a, b))


def search_similar(
    query_embedding: np.ndarray,
    case_features: np.ndarray,
    cases: list[dict],
    top_k: int = TOP_K_CASES,
) -> list[dict]:
    """
    Search for top-K most similar cases by cosine similarity.

    Args:
        query_embedding: (768,) query image embedding.
        case_features: (N, 768) pre-computed case embeddings.
        cases: List of case dicts.
        top_k: Number of results.

    Returns:
        List of case dicts with added 'similarity' field, sorted by similarity desc.
    """
    if case_features.shape[0] == 0:
        return []

    # Compute all cosine similarities (features should be normalized)
    sims = case_features @ query_embedding

    # Get top-K indices
    k = min(top_k, len(cases))
    top_indices = np.argsort(sims)[-k:][::-1]

    results = []
    for idx in top_indices:
        case = dict(cases[idx])
        case["similarity"] = round(float(sims[idx]), 4)
        results.append(case)

    return results


def compute_case_statistics(similar_cases: list[dict]) -> dict:
    """Compute aggregate statistics from similar cases."""
    if not similar_cases:
        return {"total_similar": 0, "note": "无相似案例"}

    total = len(similar_cases)
    cut_up = sum(1 for c in similar_cases if c.get("final_result") == "cut_up")
    cut_even = sum(1 for c in similar_cases if c.get("final_result") == "cut_even")
    cut_down = sum(1 for c in similar_cases if c.get("final_result") == "cut_down")

    # Water type stats
    water_counts = {}
    for c in similar_cases:
        w = c.get("output_water", "未知")
        water_counts[w] = water_counts.get(w, 0) + 1

    return {
        "total_similar": total,
        "cut_up": cut_up,
        "cut_even": cut_even,
        "cut_down": cut_down,
        "cut_up_rate": round(cut_up / total, 2) if total > 0 else 0.0,
        "water_distribution": water_counts,
        "note": f"{total}个案例统计意义有限, 仅供方向性参考" if total < 20 else f"基于{total}个相似案例"
    }


def precompute_features(cases: list[dict], image_dir: Path) -> np.ndarray:
    """
    Pre-compute Chinese-CLIP features for all cases.
    Returns (N, 768) numpy array. Falls back to pseudo-features if CLIP unavailable.
    """
    features = []
    for case in cases:
        # Look for case images
        case_id = case["id"]
        case_images = sorted(image_dir.glob(f"case_{case_id}_*"))
        if case_images:
            paths = [str(p) for p in case_images]
            emb = compute_embedding(paths)
        else:
            # No images — use deterministic pseudo-embedding based on case content
            seed_str = json.dumps(case, sort_keys=True, ensure_ascii=False)
            rng = random.Random(hash(seed_str) % (2**31))
            emb = np.array([rng.random() for _ in range(768)], dtype=np.float32)
            emb = emb / np.linalg.norm(emb)
        features.append(emb)

    if features:
        return np.stack(features)
    return np.empty((0, 768), dtype=np.float32)
