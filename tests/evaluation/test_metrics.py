"""Comprehensive unit tests for evaluation metrics calculation (Member 4 - Nancy)."""

import pytest
from src.pii_guard.reporting.metrics import (
    calculate_evaluation_metrics,
    EntityAnnotation,
    MatchingStrategy,
)


def test_perfect_matching():
    """Identical predictions and ground truth yield 100% across all metrics."""
    gt = [
        EntityAnnotation(type="EMAIL", start=10, end=30),
        EntityAnnotation(type="PHONE", start=45, end=55),
    ]
    preds = [
        EntityAnnotation(type="EMAIL", start=10, end=30, confidence=0.95),
        EntityAnnotation(type="PHONE", start=45, end=55, confidence=0.90),
    ]

    res = calculate_evaluation_metrics(preds, gt, strategy=MatchingStrategy.EXACT)
    assert res.true_positives == 2
    assert res.false_positives == 0
    assert res.false_negatives == 0
    assert res.precision == 1.0
    assert res.recall == 1.0
    assert res.f1_score == 1.0
    assert res.false_negative_rate == 0.0


def test_zero_denominator_both_empty():
    """Empty predictions and empty ground truth yield 1.0 without dividing by zero."""
    res = calculate_evaluation_metrics([], [], strategy=MatchingStrategy.EXACT)
    assert res.true_positives == 0
    assert res.false_positives == 0
    assert res.false_negatives == 0
    assert res.precision == 1.0
    assert res.recall == 1.0
    assert res.f1_score == 1.0
    assert res.false_negative_rate == 0.0


def test_zero_predictions_with_gt():
    """When detector predicts nothing but GT exists: precision=0, recall=0, fnr=1.0."""
    gt = [EntityAnnotation(type="PERSON", start=5, end=15)]
    res = calculate_evaluation_metrics([], gt, strategy=MatchingStrategy.EXACT)
    assert res.true_positives == 0
    assert res.false_positives == 0
    assert res.false_negatives == 1
    assert res.precision == 0.0
    assert res.recall == 0.0
    assert res.f1_score == 0.0
    assert res.false_negative_rate == 1.0


def test_predictions_with_empty_gt():
    """When detector fires false alarms on clean document: precision=0, recall=0, fnr=0."""
    preds = [EntityAnnotation(type="EMAIL", start=10, end=25)]
    res = calculate_evaluation_metrics(preds, [], strategy=MatchingStrategy.EXACT)
    assert res.true_positives == 0
    assert res.false_positives == 1
    assert res.false_negatives == 0
    assert res.precision == 0.0
    assert res.recall == 0.0
    assert res.f1_score == 0.0
    assert res.false_negative_rate == 0.0


def test_duplicate_predictions_deduplicated():
    """Duplicate predictions at identical spans are deduplicated to prevent double-counting."""
    gt = [EntityAnnotation(type="EMAIL", start=10, end=30)]
    preds = [
        EntityAnnotation(type="EMAIL", start=10, end=30, confidence=0.8),
        EntityAnnotation(type="EMAIL", start=10, end=30, confidence=0.9),  # Duplicate span
    ]

    res = calculate_evaluation_metrics(preds, gt, strategy=MatchingStrategy.EXACT)
    assert res.evaluated_predictions_count == 1
    assert res.true_positives == 1
    assert res.false_positives == 0
    assert res.precision == 1.0


def test_category_mismatch():
    """Exact character boundaries with wrong category must count as FP and FN."""
    gt = [EntityAnnotation(type="PERSON", start=10, end=25)]
    preds = [EntityAnnotation(type="ORGANIZATION", start=10, end=25)]

    res = calculate_evaluation_metrics(preds, gt, strategy=MatchingStrategy.EXACT)
    assert res.true_positives == 0
    assert res.false_positives == 1
    assert res.false_negatives == 1
    assert res.precision == 0.0
    assert res.recall == 0.0


def test_matching_strategies_overlap_vs_exact():
    """Partial overlap matches under OVERLAP but fails under EXACT."""
    gt = [EntityAnnotation(type="ADDRESS", start=100, end=140)]
    preds = [EntityAnnotation(type="ADDRESS", start=105, end=140)]  # Missing first 5 chars

    exact_res = calculate_evaluation_metrics(preds, gt, strategy=MatchingStrategy.EXACT)
    assert exact_res.true_positives == 0
    assert exact_res.false_positives == 1
    assert exact_res.false_negatives == 1

    overlap_res = calculate_evaluation_metrics(preds, gt, strategy=MatchingStrategy.OVERLAP)
    assert overlap_res.true_positives == 1
    assert overlap_res.false_positives == 0
    assert overlap_res.false_negatives == 0


def test_iou_50_strategy():
    """IoU >= 0.5 matches under IOU_50; IoU < 0.5 fails."""
    # GT: [0, 100), Pred1: [0, 60) -> Intersection: 60, Union: 100 -> IoU: 0.60 (PASS)
    gt = [EntityAnnotation(type="PERSON", start=0, end=100)]
    pred_pass = [EntityAnnotation(type="PERSON", start=0, end=60)]
    res_pass = calculate_evaluation_metrics(pred_pass, gt, strategy=MatchingStrategy.IOU_50)
    assert res_pass.true_positives == 1

    # Pred2: [0, 30) -> Intersection: 30, Union: 100 -> IoU: 0.30 (FAIL)
    pred_fail = [EntityAnnotation(type="PERSON", start=0, end=30)]
    res_fail = calculate_evaluation_metrics(pred_fail, gt, strategy=MatchingStrategy.IOU_50)
    assert res_fail.true_positives == 0


def test_invalid_span_boundary_raises_error():
    """Spans with start >= end must raise a clear ValueError."""
    with pytest.raises(ValueError, match="Invalid span boundary"):
        calculate_evaluation_metrics(
            [{"type": "EMAIL", "start": 50, "end": 40}],  # Invalid inverted
            [],
        )


def test_category_breakdown_detail():
    """Category breakdown computes per-type precision, recall, and FNR."""
    gt = [
        EntityAnnotation(type="EMAIL", start=10, end=20),
        EntityAnnotation(type="PHONE", start=30, end=40),
    ]
    preds = [
        EntityAnnotation(type="EMAIL", start=10, end=20),  # TP
        # PHONE missed -> FN
        EntityAnnotation(type="PERSON", start=50, end=60),  # FP
    ]

    res = calculate_evaluation_metrics(preds, gt, strategy=MatchingStrategy.EXACT)
    assert "EMAIL" in res.category_breakdown
    assert "PHONE" in res.category_breakdown
    assert "PERSON" in res.category_breakdown

    assert res.category_breakdown["EMAIL"].precision == 1.0
    assert res.category_breakdown["EMAIL"].recall == 1.0

    assert res.category_breakdown["PHONE"].recall == 0.0
    assert res.category_breakdown["PHONE"].false_negative_rate == 1.0

    assert res.category_breakdown["PERSON"].precision == 0.0
