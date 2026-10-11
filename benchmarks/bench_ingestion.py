"""Performance benchmark for document ingestion throughput and latency."""

import sys
import time
import os
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pii_guard.ingestion import extract_document, IngestionConfig

BENCH_FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "ingestion"


def run_benchmark() -> List[Dict[str, Any]]:
    test_files = [
        ("PDF (Digital Text)", BENCH_FIXTURES / "clean_text.pdf"),
        ("PDF (Scanned OCR)", BENCH_FIXTURES / "scanned_page.pdf"),
        ("PDF (Mixed Digital+OCR)", BENCH_FIXTURES / "mixed.pdf"),
        ("DOCX (Interleaved)", BENCH_FIXTURES / "sample.docx"),
        ("PPTX (Shapes & Notes)", BENCH_FIXTURES / "sample.pptx"),
        ("TXT (UTF-8)", BENCH_FIXTURES / "utf8.txt"),
    ]

    results = []
    cfg = IngestionConfig()

    print("=" * 80)
    print("PII GUARD INGESTION THROUGHPUT BENCHMARK")
    print("=" * 80)
    print(f"{'Format / Test File':<26} | {'Pages':<6} | {'Size (KB)':<10} | {'Time (s)':<9} | {'Pages/sec':<10} | {'Status'}")
    print("-" * 80)

    for label, path in test_files:
        if not path.exists():
            print(f"Skipping {label}: file not found at {path}")
            continue

        file_size_kb = path.stat().st_size / 1024.0

        # Warm-up pass
        extract_document(str(path), config=cfg)

        # Timed passes (3 iterations)
        times = []
        doc = None
        for _ in range(3):
            t0 = time.perf_counter()
            doc = extract_document(str(path), config=cfg)
            t1 = time.perf_counter()
            times.append(t1 - t0)

        avg_time = sum(times) / len(times)
        num_pages = max(1, len(doc.pages))
        pages_per_sec = num_pages / avg_time
        mb_per_sec = (file_size_kb / 1024.0) / avg_time

        res = {
            "label": label,
            "filename": path.name,
            "pages": num_pages,
            "size_kb": round(file_size_kb, 2),
            "avg_time_sec": round(avg_time, 4),
            "pages_per_sec": round(pages_per_sec, 2),
            "mb_per_sec": round(mb_per_sec, 2),
            "status": doc.extraction_status,
        }
        results.append(res)

        print(
            f"{label:<26} | {num_pages:<6} | {file_size_kb:<10.1f} | {avg_time:<9.4f} | {pages_per_sec:<10.2f} | {doc.extraction_status}"
        )

    print("-" * 80)
    return results


if __name__ == "__main__":
    run_benchmark()
