"""
Case store: JSON-backed case management with embedding matrix.
"""

import json
from pathlib import Path
from typing import Optional

import numpy as np

from config import CASES_FILE, FEATURES_FILE, IMAGES_DIR
from services.clip_embedding import precompute_features, search_similar, compute_case_statistics


class CaseStore:
    """Manages the case database."""

    def __init__(self):
        self._cases: list[dict] = []
        self._features: Optional[np.ndarray] = None
        self._load()

    def _load(self):
        """Load cases from JSON file and features from numpy file."""
        if CASES_FILE.exists():
            with open(CASES_FILE, "r", encoding="utf-8") as f:
                self._cases = json.load(f)

        if FEATURES_FILE.exists() and FEATURES_FILE.stat().st_size > 0:
            self._features = np.load(FEATURES_FILE)
        else:
            self._features = np.empty((0, 768), dtype=np.float32)

    def _save(self):
        """Save cases to JSON."""
        with open(CASES_FILE, "w", encoding="utf-8") as f:
            json.dump(self._cases, f, ensure_ascii=False, indent=2)

    @property
    def cases(self) -> list[dict]:
        return self._cases

    @property
    def features(self) -> np.ndarray:
        if self._features is None:
            self._features = np.empty((0, 768), dtype=np.float32)
        return self._features

    def count(self) -> int:
        return len(self._cases)

    def get(self, case_id: int) -> Optional[dict]:
        for c in self._cases:
            if c["id"] == case_id:
                return c
        return None

    def add(self, case: dict) -> dict:
        """Add a new case and re-index."""
        # Assign ID
        existing_ids = {c["id"] for c in self._cases}
        new_id = max(existing_ids) + 1 if existing_ids else 1
        case["id"] = new_id
        self._cases.append(case)
        self._save()
        self._rebuild_features()
        return case

    def delete(self, case_id: int) -> bool:
        """Delete a case by ID."""
        before = len(self._cases)
        self._cases = [c for c in self._cases if c["id"] != case_id]
        if len(self._cases) < before:
            self._save()
            self._rebuild_features()
            return True
        return False

    def _rebuild_features(self):
        """Rebuild the feature matrix from current cases."""
        self._features = precompute_features(self._cases, IMAGES_DIR)
        if self._features.shape[0] > 0:
            np.save(FEATURES_FILE, self._features)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> tuple[list[dict], dict]:
        """
        Search for similar cases and return (cases, statistics).

        Args:
            query_embedding: Normalized (768,) image embedding.
            top_k: Number of results.

        Returns:
            (similar_cases, case_statistics)
        """
        similar = search_similar(query_embedding, self.features, self._cases, top_k)
        stats = compute_case_statistics(similar)
        return similar, stats

    def rebuild(self):
        """Force rebuild of all features."""
        self._rebuild_features()


# Global singleton
case_store = CaseStore()
