"""Evaluation metrics subsystem for PII detection assessment (Member 4 - Nancy).

PRIVACY & RIGOR RULES:
1. Compares predictions with ground truth annotations based on formal character span geometry.
2. Never prints, stores, or logs the sensitive text content of evaluated spans.
3. Explicitly handles zero-denominators, overlapping spans, category mismatches, and duplicates.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field, ConfigDict

from ..orchestration.models import DetectedEntity


class MatchingStrategy(str, Enum):
    """Span boundary matching policy."""
    EXACT = "exact"      # start == gt.start and end == gt.end and type == gt.type
    OVERLAP = "overlap"  # intersection(start, end) > 0 and type == gt.type
    IOU_50 = "iou_50"    # Intersection-over-Union >= 0.50 and type == gt.type


class EntityAnnotation(BaseModel):
    """Ground truth or predicted span annotation for evaluation."""
    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., description="Entity category name (e.g. EMAIL, PERSON)")
    start: int = Field(..., ge=0, description="0-based start character offset")
    end: int = Field(..., ge=0, description="0-based end character offset (exclusive)")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class CategoryMetricBreakdown(BaseModel):
    """Metrics calculated for a single PII category."""
    model_config = ConfigDict(extra="forbid")

    category: str
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    false_negative_rate: float


class DetectionMetricResult(BaseModel):
    """Aggregated evaluation results across all categories."""
    model_config = ConfigDict(extra="forbid")

    matching_strategy: MatchingStrategy
    evaluated_predictions_count: int
    evaluated_ground_truth_count: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    false_negative_rate: float
    category_breakdown: Dict[str, CategoryMetricBreakdown] = Field(default_factory=dict)

    def to_safe_dict(self) -> Dict[str, Any]:
        """Serialize metrics to a safe summary dictionary."""
        return {
            "matching_strategy": self.matching_strategy.value,
            "evaluated_predictions_count": self.evaluated_predictions_count,
            "evaluated_ground_truth_count": self.evaluated_ground_truth_count,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "false_negative_rate": round(self.false_negative_rate, 4),
            "categories": {
                k: {
                    "tp": v.true_positives,
                    "fp": v.false_positives,
                    "fn": v.false_negatives,
                    "precision": round(v.precision, 4),
                    "recall": round(v.recall, 4),
                    "f1": round(v.f1_score, 4),
                    "fnr": round(v.false_negative_rate, 4),
                }
                for k, v in self.category_breakdown.items()
            },
        }


def _calculate_iou(start1: int, end1: int, start2: int, end2: int) -> float:
    """Calculate 1D intersection over union between two character intervals."""
    inter_start = max(start1, start2)
    inter_end = min(end1, end2)
    intersection = max(0, inter_end - inter_start)
    if intersection == 0:
        return 0.0
    union = (end1 - start1) + (end2 - start2) - intersection
    return float(intersection) / float(union) if union > 0 else 0.0


def _is_match(
    pred: EntityAnnotation, gt: EntityAnnotation, strategy: MatchingStrategy
) -> bool:
    """Determine if a prediction matches ground truth according to strategy."""
    if pred.type.upper() != gt.type.upper():
        return False

    if strategy == MatchingStrategy.EXACT:
        return pred.start == gt.start and pred.end == gt.end
    elif strategy == MatchingStrategy.OVERLAP:
        return max(pred.start, gt.start) < min(pred.end, gt.end)
    elif strategy == MatchingStrategy.IOU_50:
        return _calculate_iou(pred.start, pred.end, gt.start, gt.end) >= 0.50

    return False


def calculate_evaluation_metrics(
    predictions: List[Union[EntityAnnotation, DetectedEntity, Dict[str, Any]]],
    ground_truth: List[Union[EntityAnnotation, Dict[str, Any]]],
    strategy: MatchingStrategy = MatchingStrategy.EXACT,
) -> DetectionMetricResult:
    """Compute precision, recall, F1, and FNR with bipartite matching and deduplication.
    
    Zero Denominator Convention:
    - If TP + FP == 0 and TP + FN == 0 (no predictions and no GT): precision=1.0, recall=1.0, F1=1.0, FNR=0.0
    - If TP + FP == 0 and TP + FN > 0 (no predictions, GT exists): precision=0.0, recall=0.0, F1=0.0, FNR=1.0
    - If TP + FP > 0 and TP + FN == 0 (predictions exist, GT empty): precision=0.0, recall=0.0, F1=0.0, FNR=0.0
    """
    # 1. Normalize and validate input objects
    norm_preds: List[EntityAnnotation] = []
    for p in predictions:
        if isinstance(p, EntityAnnotation):
            ann = p
        elif isinstance(p, DetectedEntity):
            ann = EntityAnnotation(type=p.type, start=p.start, end=p.end, confidence=p.confidence)
        elif isinstance(p, dict):
            ann = EntityAnnotation(
                type=str(p["type"]),
                start=int(p["start"]),
                end=int(p["end"]),
                confidence=float(p.get("confidence", 1.0)),
            )
        else:
            raise ValueError(f"Unsupported prediction type: {type(p)}")
        if ann.end <= ann.start:
            raise ValueError(f"Invalid span boundary: start={ann.start} >= end={ann.end}")
        norm_preds.append(ann)

    norm_gt: List[EntityAnnotation] = []
    for g in ground_truth:
        if isinstance(g, EntityAnnotation):
            ann = g
        elif isinstance(g, dict):
            ann = EntityAnnotation(
                type=str(g["type"]),
                start=int(g["start"]),
                end=int(g["end"]),
                confidence=float(g.get("confidence", 1.0)),
            )
        else:
            raise ValueError(f"Unsupported ground truth type: {type(g)}")
        if ann.end <= ann.start:
            raise ValueError(f"Invalid ground truth span boundary: start={ann.start} >= end={ann.end}")
        norm_gt.append(ann)

    # 2. Deduplicate spans while preserving ordering
    dedup_preds: List[EntityAnnotation] = []
    seen_pred: Set[Tuple[str, int, int]] = set()
    for p in norm_preds:
        key = (p.type.upper(), p.start, p.end)
        if key not in seen_pred:
            seen_pred.add(key)
            dedup_preds.append(p)

    dedup_gt: List[EntityAnnotation] = []
    seen_gt: Set[Tuple[str, int, int]] = set()
    for g in norm_gt:
        key = (g.type.upper(), g.start, g.end)
        if key not in seen_gt:
            seen_gt.add(key)
            dedup_gt.append(g)

    # Collect all unique categories
    all_categories = sorted(
        list(set([p.type.upper() for p in dedup_preds] + [g.type.upper() for g in dedup_gt]))
    )

    # 3. Overall greedy bipartite matching
    # Sort predictions by confidence descending (if available) for stable matching
    sorted_preds = sorted(dedup_preds, key=lambda x: (x.confidence or 0.0), reverse=True)

    matched_gt_indices: Set[int] = set()
    tp = 0
    fp = 0

    for pred in sorted_preds:
        match_idx = None
        for i, gt in enumerate(dedup_gt):
            if i not in matched_gt_indices and _is_match(pred, gt, strategy):
                match_idx = i
                break
        if match_idx is not None:
            matched_gt_indices.add(match_idx)
            tp += 1
        else:
            fp += 1

    fn = len(dedup_gt) - len(matched_gt_indices)

    # 4. Overall metrics calculation
    if tp + fp == 0 and tp + fn == 0:
        precision = 1.0
        recall = 1.0
        f1 = 1.0
        fnr = 0.0
    else:
        precision = float(tp) / float(tp + fp) if (tp + fp) > 0 else 0.0
        recall = float(tp) / float(tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        fnr = float(fn) / float(tp + fn) if (tp + fn) > 0 else 0.0

    # 5. Category-wise breakdown
    category_breakdown: Dict[str, CategoryMetricBreakdown] = {}
    for cat in all_categories:
        cat_preds = [p for p in dedup_preds if p.type.upper() == cat]
        cat_gt = [g for g in dedup_gt if g.type.upper() == cat]

        cat_matched_gt: Set[int] = set()
        cat_tp = 0
        cat_fp = 0

        for p in cat_preds:
            match_idx = None
            for j, g in enumerate(cat_gt):
                if j not in cat_matched_gt and _is_match(p, g, strategy):
                    match_idx = j
                    break
            if match_idx is not None:
                cat_matched_gt.add(match_idx)
                cat_tp += 1
            else:
                cat_fp += 1

        cat_fn = len(cat_gt) - len(cat_matched_gt)

        if cat_tp + cat_fp == 0 and cat_tp + cat_fn == 0:
            cat_p = 1.0
            cat_r = 1.0
            cat_f1 = 1.0
            cat_fnr = 0.0
        else:
            cat_p = float(cat_tp) / float(cat_tp + cat_fp) if (cat_tp + cat_fp) > 0 else 0.0
            cat_r = float(cat_tp) / float(cat_tp + cat_fn) if (cat_tp + cat_fn) > 0 else 0.0
            cat_f1 = (2 * cat_p * cat_r) / (cat_p + cat_r) if (cat_p + cat_r) > 0 else 0.0
            cat_fnr = float(cat_fn) / float(cat_tp + cat_fn) if (cat_tp + cat_fn) > 0 else 0.0

        category_breakdown[cat] = CategoryMetricBreakdown(
            category=cat,
            true_positives=cat_tp,
            false_positives=cat_fp,
            false_negatives=cat_fn,
            precision=cat_p,
            recall=cat_r,
            f1_score=cat_f1,
            false_negative_rate=cat_fnr,
        )

    return DetectionMetricResult(
        matching_strategy=strategy,
        evaluated_predictions_count=len(dedup_preds),
        evaluated_ground_truth_count=len(dedup_gt),
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        precision=precision,
        recall=recall,
        f1_score=f1,
        false_negative_rate=fnr,
        category_breakdown=category_breakdown,
    )
