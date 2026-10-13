"""Test suite for PII detection, classification and evaluation (Member 2).

Run with:  pytest -q tests/test_detection.py
No network, no API keys, no NER model required.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from pii_guard.detection import (
    PII_TYPES,
    DetectionInputError,
    DetectionResult,
    detect_pii,
)
from pii_guard.detection.classifier import resolve_overlaps
from pii_guard.detection.ner_detector import detect_ner
from pii_guard.detection.pattern_detector import detect_patterns
from pii_guard.detection.schemas import Candidate
from pii_guard.detection.validators import (
    ipv4_valid,
    luhn_valid,
    pan_valid,
    ssn_valid,
)
from evaluation.build_ground_truth import CORPUS, render
from evaluation.metrics import evaluate, load_ground_truth, prf, detector_predictor

GROUND_TRUTH = Path(__file__).resolve().parents[1] / "evaluation" / "ground_truth.jsonl"


def doc(text, doc_id="doc-test", status="success"):
    return SimpleNamespace(document_id=doc_id, text=text, extraction_status=status)


def types_and_values(text):
    result = detect_pii(doc(text))
    return [(e.type, text[e.start:e.end]) for e in result.entities]


# ---------------------------------------------------------------------------
# 1. Validators
# ---------------------------------------------------------------------------

def test_luhn_accepts_known_valid_test_card():
    assert luhn_valid("4111111111111111")


def test_luhn_rejects_single_digit_change():
    assert not luhn_valid("4111111111111112")


def test_luhn_rejects_wrong_length_and_non_digits():
    assert not luhn_valid("4111")
    assert not luhn_valid("411111111111111X")


@pytest.mark.parametrize("value", ["123-45-6789", "512-34-5678"])
def test_ssn_valid_structure(value):
    assert ssn_valid(value)


@pytest.mark.parametrize("value", ["000-12-3456", "666-12-3456", "900-12-3456", "123-00-6789", "123-45-0000"])
def test_ssn_invalid_structure(value):
    assert not ssn_valid(value)


def test_ipv4_validator():
    assert ipv4_valid("192.0.2.44")
    assert not ipv4_valid("256.0.0.1")
    assert not ipv4_valid("1.2.3")


def test_pan_holder_type_check():
    assert pan_valid("ABCPE1234F")  # 4th char P = individual
    assert not pan_valid("ABCDE1234F")  # 4th char D is not a holder type


# ---------------------------------------------------------------------------
# 2. Pattern rules: positives and negatives
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected_type, expected_value",
    [
        ("Write to alex.rivera@example.test today.", "EMAIL", "alex.rivera@example.test"),
        ("Call +1 (415) 555-0132 now.", "PHONE", "+1 (415) 555-0132"),
        ("Call 555-013-7788 now.", "PHONE", "555-013-7788"),
        ("Call +91 98765 43210 now.", "PHONE", "+91 98765 43210"),
        ("SSN 123-45-6789 on file.", "GOVERNMENT_ID", "123-45-6789"),
        ("PAN ABCPE1234F on file.", "GOVERNMENT_ID", "ABCPE1234F"),
        ("Card 4111 1111 1111 1111 declined.", "FINANCIAL_IDENTIFIER", "4111 1111 1111 1111"),
        ("Ref EMP-10482 assigned.", "EMPLOYEE_ID", "EMP-10482"),
<<<<<<< HEAD
=======
        ("Employee CAD-EMP-83563 on site.", "EMPLOYEE_ID", "CAD-EMP-83563"),
>>>>>>> origin/feature/member5-integration
        ("From 192.0.2.44 today.", "IP_ADDRESS", "192.0.2.44"),
    ],
)
def test_each_type_detected_with_exact_value(text, expected_type, expected_value):
    found = types_and_values(text)
    assert (expected_type, expected_value) in found


@pytest.mark.parametrize(
    "text",
    [
        "Test value 666-12-3456 is not valid.",            # invalid SSN area
        "Short form 123-45-678 is not valid.",             # wrong digit count
        "Batch 4111 1111 1111 1112 was rejected.",         # fails Luhn
        "Holder code ABCDE1234F is not valid.",            # bad PAN holder type
        "Release 2.10.3 on 2026-10-12, build 1.2.3.",      # version/date strings
        "Order 1234567890123 shipped.",                    # long number, fails Luhn
        "Build 12345 and ticket 67890 merged at 10:30.",   # short digit runs
        "Reference 2026-10-12 and extension 0132 only.",   # date and extension
    ],
)
def test_near_misses_are_not_flagged(text):
    assert types_and_values(text) == []


def test_no_pii_document_returns_empty_entities_without_warnings():
    # An NER backend that finds nothing, so the only possible warning would be a spurious one.
    result = detect_pii(
        doc("The quarterly risk committee meets on Tuesday."),
        ner_backend=lambda seg: [],
    )
    assert result.entities == []
    assert result.warnings == []


def test_pattern_rules_do_not_match_inside_longer_digit_runs():
    assert detect_patterns("ID 91234567890123456789 is long.") == []


def test_card_group_does_not_absorb_trailing_text():
    text = "Card 4111 1111 1111 1111, expires 2030."
    result = detect_pii(doc(text))
    spans = [text[e.start:e.end] for e in result.entities]
    assert spans == ["4111 1111 1111 1111"]


# ---------------------------------------------------------------------------
# 3. Overlap resolution and precedence
# ---------------------------------------------------------------------------

def test_email_wins_over_ip_inside_local_part():
    text = "Owner account 10.0.0.1@example.test was flagged."
    result = detect_pii(doc(text))
    assert [(e.type, text[e.start:e.end]) for e in result.entities] == [
        ("EMAIL", "10.0.0.1@example.test")
    ]
    assert any(w.code == "OVERLAP_RESOLVED" for w in result.warnings)


def test_resolve_overlaps_prefers_higher_precedence_then_longer_span():
    person = Candidate("PERSON", 0, 10, 0.9, "ner")
    email = Candidate("EMAIL", 4, 14, 0.98, "pattern")
    kept, dropped = resolve_overlaps([person, email])
    assert [c.type for c in kept] == ["EMAIL"]
    assert dropped == 1


def test_resolve_overlaps_keeps_disjoint_spans_sorted():
    a = Candidate("PHONE", 20, 30, 0.8, "pattern")
    b = Candidate("EMAIL", 0, 10, 0.98, "pattern")
    kept, dropped = resolve_overlaps([a, b])
    assert [(c.start, c.end) for c in kept] == [(0, 10), (20, 30)]
    assert dropped == 0


def test_resolve_overlaps_is_deterministic_regardless_of_input_order():
    cands = [
        Candidate("PERSON", 0, 5, 0.6, "ner"),
        Candidate("PHONE", 3, 12, 0.8, "pattern"),
        Candidate("EMAIL", 10, 25, 0.98, "pattern"),
    ]
    first = resolve_overlaps(cands)
    second = resolve_overlaps(list(reversed(cands)))
    assert first == second


# ---------------------------------------------------------------------------
# 4. Contract B shape and offset rules
# ---------------------------------------------------------------------------

def test_result_matches_contract_b_shape():
    text = "Mail alex@example.test"
    payload = detect_pii(doc(text, doc_id="doc-001")).model_dump()
    assert set(payload) == {"document_id", "entities", "warnings"}
    assert payload["document_id"] == "doc-001"
    entity = payload["entities"][0]
    assert set(entity) == {"type", "start", "end", "confidence"}
    assert entity["type"] in PII_TYPES
    assert 0.0 <= entity["confidence"] <= 1.0


def test_offsets_are_zero_based_end_exclusive_into_exact_text():
    text = "Hi alex@example.test!"
    entity = detect_pii(doc(text)).entities[0]
    assert (entity.start, entity.end) == (3, 20)  # len('alex@example.test') == 17
    assert text[entity.start:entity.end] == "alex@example.test"


def test_detection_is_deterministic():
    text = "Card 4111 1111 1111 1111 and SSN 123-45-6789."
    assert detect_pii(doc(text)).model_dump() == detect_pii(doc(text)).model_dump()


def test_no_span_crosses_a_page_boundary():
    text = "Page one ends with alex@example.test\fPage two starts 555-013-7788"
    result = detect_pii(doc(text))
    for entity in result.entities:
        assert "\f" not in text[entity.start:entity.end]
    assert len(result.entities) == 2


def test_dropping_invalid_candidates_is_reported_without_text():
    result = detect_pii(doc("Mail alex@example.test"))
    assert all("alex" not in w.message for w in result.warnings)


# ---------------------------------------------------------------------------
# 5. Fail-closed behaviour
# ---------------------------------------------------------------------------

def test_failed_extraction_is_refused_not_reported_as_clean():
    with pytest.raises(DetectionInputError):
        detect_pii(doc("alex@example.test", status="failed"))


def test_unknown_extraction_status_is_refused():
    with pytest.raises(DetectionInputError):
        detect_pii(doc("text", status="maybe"))


def test_missing_document_id_is_refused():
    with pytest.raises(DetectionInputError):
        detect_pii(SimpleNamespace(document_id="", text="x", extraction_status="success"))


def test_partial_extraction_is_scanned_and_flagged():
    result = detect_pii(doc("Mail alex@example.test", status="partial"))
    assert [e.type for e in result.entities] == ["EMAIL"]
    assert any(w.code == "UPSTREAM_PARTIAL_EXTRACTION" for w in result.warnings)


def test_empty_text_returns_warning_not_silent_success():
    result = detect_pii(doc("   "))
    assert result.entities == []
    assert [w.code for w in result.warnings] == ["EMPTY_TEXT"]


# ---------------------------------------------------------------------------
# 6. NER adapter (PERSON), exercised with a fake backend
# ---------------------------------------------------------------------------

def test_missing_ner_backend_is_reported_explicitly():
    result = detect_pii(doc("Prepared by Julian Thorne."), ner_backend=None)
    assert [w.code for w in result.warnings] == ["NER_UNAVAILABLE"]
    assert all(e.type != "PERSON" for e in result.entities)


def _fake_backend(name):
    def backend(segment):
        start = segment.find(name)
        if start == -1:
            return []
        return [("PERSON", start, start + len(name), 0.9)]
    return backend


def test_ner_person_span_offsets_are_absolute_across_pages():
    text = "Intro page\fPrepared by Julian Thorne for audit"
    result = detect_pii(doc(text), ner_backend=_fake_backend("Julian Thorne"))
    person = [e for e in result.entities if e.type == "PERSON"]
    assert len(person) == 1
    assert text[person[0].start:person[0].end] == "Julian Thorne"


def test_ner_label_outside_taxonomy_is_ignored():
    segments, warnings = detect_ner(
        "Based in Chennai",
        lambda seg: [("GPE", 9, 16, 0.9)],
    )
    assert segments == []
    assert warnings == []


def test_ner_person_inside_email_is_suppressed_by_precedence():
    text = "Contact alex.example@example.test today"
    backend = _fake_backend("alex.example")
    result = detect_pii(doc(text), ner_backend=backend)
    assert [e.type for e in result.entities] == ["EMAIL"]


# ---------------------------------------------------------------------------
# 7. Ground truth and metrics
# ---------------------------------------------------------------------------

def test_ground_truth_file_is_in_sync_with_annotation_source():
    expected = []
    for doc_id, markup in CORPUS:
        text, entities = render(markup)
        expected.append({"doc_id": doc_id, "text": text, "entities": entities})
    actual = load_ground_truth(GROUND_TRUTH)
    assert actual == expected


def test_every_ground_truth_span_matches_its_annotated_value():
    for record in load_ground_truth(GROUND_TRUTH):
        for entity in record["entities"]:
            assert record["text"][entity["start"]:entity["end"]] == entity["value"]
            assert entity["type"] in PII_TYPES


def test_ground_truth_covers_negatives_and_multi_page_cases():
    records = load_ground_truth(GROUND_TRUTH)
    assert len(records) >= 20
    assert any(r["entities"] == [] for r in records)
    assert any("\f" in r["text"] for r in records)


def test_prf_guards_zero_denominators():
    assert prf(0, 0, 0) == {"tp": 0, "fp": 0, "fn": 0, "precision": None, "recall": None, "f1": None}
    m = prf(2, 1, 1)
    assert m["precision"] == pytest.approx(2 / 3)
    assert m["recall"] == pytest.approx(2 / 3)
    assert m["f1"] == pytest.approx(2 / 3)


def test_evaluate_counts_exact_span_and_type_matches():
    corpus = [{
        "doc_id": "x",
        "text": "abc",
        "entities": [{"type": "EMAIL", "start": 0, "end": 3}],
    }]
    report = evaluate(corpus, lambda d: [("EMAIL", 0, 3), ("PHONE", 0, 2)])
    assert report["overall"]["tp"] == 1
    assert report["overall"]["fp"] == 1
    assert report["overall"]["fn"] == 0
    assert report["false_positives"] == [("x", "PHONE", 0, 2)]


def test_evaluate_excludes_skipped_types_from_scoring():
    corpus = [{
        "doc_id": "x",
        "text": "Julian Thorne",
        "entities": [{"type": "PERSON", "start": 0, "end": 13}],
    }]
    report = evaluate(corpus, lambda d: [], skip_types=frozenset({"PERSON"}))
    assert report["overall"]["fn"] == 0
    assert report["overall"]["recall"] is None


def test_pattern_only_ground_truth_scores_perfectly_on_current_corpus():
    """Regression guard, not a quality claim: the corpus was written alongside the rules.

    A hold-out set written independently of the rules is still needed before
    reporting these numbers as generalisation performance.
    """
    report = evaluate(
        load_ground_truth(GROUND_TRUTH),
        detector_predictor(None),
        skip_types=frozenset({"PERSON", "ADDRESS"}),
    )
    assert report["overall"]["fn"] == 0
    assert report["overall"]["fp"] == 0
<<<<<<< HEAD
=======


def test_resolve_overlaps_unknown_candidate_type():
    from src.pii_guard.detection.classifier import resolve_overlaps
    from src.pii_guard.detection.schemas import Candidate
    candidates = [
        Candidate(type="UNKNOWN_CUSTOM_TYPE", start=0, end=10, confidence=0.8, source="test"),
        Candidate(type="EMAIL", start=5, end=15, confidence=0.98, source="test"),
    ]
    accepted, dropped = resolve_overlaps(candidates)
    assert len(accepted) == 1
    assert accepted[0].type == "EMAIL"
    assert dropped == 1


def test_ssn_valid_malformed_inputs():
    from src.pii_guard.detection.validators import ssn_valid
    assert not ssn_valid("")
    assert not ssn_valid("123-45")
    assert not ssn_valid("123-45-6789-extra")
    assert not ssn_valid("abc-de-fghi")
>>>>>>> origin/feature/member5-integration
