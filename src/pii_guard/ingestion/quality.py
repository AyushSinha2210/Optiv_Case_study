"""Extraction-quality metrics: completeness and structure preservation scoring."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import rapidfuzz

from .schemas import ExtractedDocument


class GroundTruthStructure(BaseModel):
    """Ground truth expectations for synthetic fixtures to benchmark extraction."""
    expected_text: str
    expected_pages: int
    headings: List[str] = Field(default_factory=list)
    paragraphs: List[str] = Field(default_factory=list)
    table_rows: List[str] = Field(default_factory=list)
    reading_order_anchors: List[str] = Field(default_factory=list)


class QualityMetrics(BaseModel):
    """Detailed score report of extraction fidelity against ground truth."""
    completeness: float = Field(
        ..., description="Normalized lexical similarity (0.0 - 100.0) via RapidFuzz"
    )
    structure_score: float = Field(
        ..., description="Weighted structural retention percentage (0.0 - 100.0)"
    )
    boundary_score: float = Field(..., description="Page / slide boundary retention (0 - 100)")
    heading_score: float = Field(..., description="Heading detection score (0 - 100)")
    paragraph_score: float = Field(..., description="Paragraph integrity score (0 - 100)")
    table_score: float = Field(..., description="Table row / cell structure score (0 - 100)")
    reading_order_score: float = Field(..., description="Sequential reading order score (0 - 100)")
    overall_quality: float = Field(..., description="Composite quality index (0.0 - 100.0)")

    def passes_threshold(self, min_structure: float = 80.0) -> bool:
        """Verify whether structural retention satisfies the case study threshold."""
        return self.structure_score >= min_structure


def calculate_quality_metrics(
    extracted_doc: ExtractedDocument, ground_truth: GroundTruthStructure
) -> QualityMetrics:
    """Calculate quantitative completeness and weighted structural retention scores.

    Weights:
    - Page/Slide Boundary Retention: 25%
    - Heading Retention: 25%
    - Paragraph Integrity: 20%
    - Table Structure Retention: 20%
    - Reading Order Flow: 10%
    """
    extracted_text = extracted_doc.text

    # 1. Lexical Completeness (RapidFuzz token set ratio)
    if not ground_truth.expected_text.strip():
        completeness = 100.0 if not extracted_text.strip() else 0.0
    else:
        completeness = float(
            rapidfuzz.fuzz.token_set_ratio(
                ground_truth.expected_text, extracted_text
            )
        )

    # 2. Boundary score (page / slide count fidelity)
    if ground_truth.expected_pages > 0:
        actual_pages = len(extracted_doc.pages)
        diff = abs(actual_pages - ground_truth.expected_pages)
        boundary_score = max(0.0, 100.0 - (diff / ground_truth.expected_pages) * 100.0)
    else:
        boundary_score = 100.0

    # 3. Heading score
    if ground_truth.headings:
        found_headings = 0
        for h in ground_truth.headings:
            # Check presence with fuzzy matching threshold >= 85
            ratio = rapidfuzz.fuzz.partial_ratio(h, extracted_text)
            if ratio >= 85:
                found_headings += 1
        heading_score = (found_headings / len(ground_truth.headings)) * 100.0
    else:
        heading_score = 100.0

    # 4. Paragraph score
    if ground_truth.paragraphs:
        found_paras = 0
        for p in ground_truth.paragraphs:
            ratio = rapidfuzz.fuzz.partial_ratio(p, extracted_text)
            if ratio >= 80:
                found_paras += 1
        paragraph_score = (found_paras / len(ground_truth.paragraphs)) * 100.0
    else:
        paragraph_score = 100.0

    # 5. Table score
    if ground_truth.table_rows:
        found_rows = 0
        for r in ground_truth.table_rows:
            ratio = rapidfuzz.fuzz.partial_ratio(r, extracted_text)
            if ratio >= 80:
                found_rows += 1
        table_score = (found_rows / len(ground_truth.table_rows)) * 100.0
    else:
        table_score = 100.0

    # 6. Reading order score (anchor sequence checking)
    if len(ground_truth.reading_order_anchors) >= 2:
        last_pos = -1
        correct_transitions = 0
        total_transitions = len(ground_truth.reading_order_anchors) - 1

        for anchor in ground_truth.reading_order_anchors:
            pos = extracted_text.find(anchor)
            if pos != -1 and pos > last_pos:
                if last_pos != -1:
                    correct_transitions += 1
                last_pos = pos
            elif pos != -1:
                last_pos = pos

        reading_order_score = (
            (correct_transitions / total_transitions) * 100.0 if total_transitions > 0 else 100.0
        )
    else:
        reading_order_score = 100.0

    # Weighted structure score: 0.25, 0.25, 0.20, 0.20, 0.10
    structure_score = (
        0.25 * boundary_score
        + 0.25 * heading_score
        + 0.20 * paragraph_score
        + 0.20 * table_score
        + 0.10 * reading_order_score
    )

    overall_quality = 0.5 * completeness + 0.5 * structure_score

    return QualityMetrics(
        completeness=round(completeness, 2),
        structure_score=round(structure_score, 2),
        boundary_score=round(boundary_score, 2),
        heading_score=round(heading_score, 2),
        paragraph_score=round(paragraph_score, 2),
        table_score=round(table_score, 2),
        reading_order_score=round(reading_order_score, 2),
        overall_quality=round(overall_quality, 2),
    )
