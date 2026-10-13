"""Member 2 evaluation: exact-span plus entity-type matching on synthetic ground truth.

    precision = TP / (TP + FP)
    recall    = TP / (TP + FN)
    F1        = 2 * precision * recall / (precision + recall)

A metric whose denominator is zero is reported as None (n/a), not as 0.
Types that depend on an NER backend are excluded when that backend is absent,
so a missing model is not scored as a recall failure.

Run from the repository root:
    python -m evaluation.metrics
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
GROUND_TRUTH = Path(__file__).resolve().parent / "ground_truth.jsonl"
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from pii_guard.detection import detect_pii, load_spacy_backend  # noqa: E402
from pii_guard.detection.ner_detector import NerBackend  # noqa: E402

NER_DEPENDENT_TYPES = frozenset({"PERSON", "ADDRESS"})

Span = tuple[str, int, int]
Predictor = Callable[[dict], Iterable[Span]]


def load_ground_truth(path: Path = GROUND_TRUTH) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    if precision is None or recall is None:
        f1 = None
    elif precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def evaluate(corpus: list[dict], predict: Predictor, skip_types: frozenset = frozenset()) -> dict:
    tp: dict[str, int] = {}
    fp: dict[str, int] = {}
    fn: dict[str, int] = {}
    false_positives: list[tuple[str, str, int, int]] = []
    false_negatives: list[tuple[str, str, int, int]] = []
    gold_total = 0

    for doc in corpus:
        gold = {
            (e["type"], e["start"], e["end"])
            for e in doc["entities"]
            if e["type"] not in skip_types
        }
        predicted = {span for span in predict(doc) if span[0] not in skip_types}
        gold_total += len(gold)

        for pii_type, start, end in gold & predicted:
            tp[pii_type] = tp.get(pii_type, 0) + 1
        for pii_type, start, end in predicted - gold:
            fp[pii_type] = fp.get(pii_type, 0) + 1
            false_positives.append((doc["doc_id"], pii_type, start, end))
        for pii_type, start, end in gold - predicted:
            fn[pii_type] = fn.get(pii_type, 0) + 1
            false_negatives.append((doc["doc_id"], pii_type, start, end))

    types = sorted(set(tp) | set(fp) | set(fn))
    per_type = {t: prf(tp.get(t, 0), fp.get(t, 0), fn.get(t, 0)) for t in types}
    overall = prf(sum(tp.values()), sum(fp.values()), sum(fn.values()))

    return {
        "documents": len(corpus),
        "gold_entities": gold_total,
        "overall": overall,
        "per_type": per_type,
        "false_positives": sorted(false_positives),
        "false_negatives": sorted(false_negatives),
        "skipped_types": sorted(skip_types),
    }


def detector_predictor(ner_backend: Optional[NerBackend]) -> Predictor:
    def predict(doc: dict) -> list[Span]:
        document = SimpleNamespace(
            document_id=doc["doc_id"], text=doc["text"], extraction_status="success"
        )
        result = detect_pii(document, ner_backend=ner_backend)
        return [(e.type, e.start, e.end) for e in result.entities]

    return predict


def _fmt(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def format_report(report: dict) -> str:
    lines = [
        f"Documents: {report['documents']}   Gold entities scored: {report['overall']['tp'] + report['overall']['fn']}",
        "",
        f"{'Type':<24}{'TP':>5}{'FP':>5}{'FN':>5}{'Precision':>11}{'Recall':>9}{'F1':>8}",
    ]
    for pii_type, m in report["per_type"].items():
        lines.append(
            f"{pii_type:<24}{m['tp']:>5}{m['fp']:>5}{m['fn']:>5}"
            f"{_fmt(m['precision']):>11}{_fmt(m['recall']):>9}{_fmt(m['f1']):>8}"
        )
    o = report["overall"]
    lines.append("-" * 67)
    lines.append(
        f"{'OVERALL':<24}{o['tp']:>5}{o['fp']:>5}{o['fn']:>5}"
        f"{_fmt(o['precision']):>11}{_fmt(o['recall']):>9}{_fmt(o['f1']):>8}"
    )
    if report["skipped_types"]:
        lines.append(f"Excluded (no NER backend): {', '.join(report['skipped_types'])}")
    lines.append("")
    for label, rows in (
        ("False negatives", report["false_negatives"]),
        ("False positives", report["false_positives"]),
    ):
        lines.append(f"{label} (doc, type, start, end):")
        if not rows:
            lines.append("  none")
        lines.extend(f"  {row}" for row in rows)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PII detection on synthetic ground truth.")
    parser.add_argument("--no-ner", action="store_true", help="Skip the NER backend even if installed.")
    args = parser.parse_args()

    backend = None if args.no_ner else load_spacy_backend()
    skip = frozenset() if backend is not None else NER_DEPENDENT_TYPES
    report = evaluate(load_ground_truth(), detector_predictor(backend), skip_types=skip)
    print(format_report(report))


if __name__ == "__main__":
    main()
