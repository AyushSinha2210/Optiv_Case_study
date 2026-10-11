"""Command-line interface for the document ingestion module."""

import sys
import json
import argparse
from pathlib import Path

from .extractor import extract_document


def main():
    parser = argparse.ArgumentParser(
        description="PII Guard Document Ingestion and Text Extraction CLI"
    )
    parser.add_argument("file_path", help="Path to document file to extract")
    parser.add_argument(
        "--json", action="store_true", help="Output full ExtractedDocument JSON"
    )
    parser.add_argument(
        "--show-text", action="store_true", help="Include extracted text in console output"
    )

    args = parser.parse_args()
    doc = extract_document(args.file_path)

    if args.json:
        data = doc.to_dict()
        if not args.show_text:
            data["text"] = f"[REDACTED_FOR_DISPLAY: {len(doc.text)} characters]"
        print(json.dumps(data, indent=2))
    else:
        print(f"Document ID:        {doc.document_id}")
        print(f"Source Type:        {doc.source_type}")
        print(f"Status:             {doc.extraction_status}")
        print(f"Pages / Slides:     {len(doc.pages)}")
        print(f"Total Characters:   {len(doc.text)}")
        if doc.warnings:
            print("Warnings / Errors:")
            for w in doc.warnings:
                p_info = f" (Page {w.page})" if w.page else ""
                print(f"  - [{w.code}]{p_info}: {w.message}")
        if args.show_text:
            print("\n--- Extracted Text ---")
            print(doc.text)


if __name__ == "__main__":
    main()
