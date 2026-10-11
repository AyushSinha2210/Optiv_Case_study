"""Deterministic, single-pass text normalization engine.

CONTRACTUAL GUARANTEE:
1. Normalization is applied ONCE inside the ingestion module before returning.
2. The returned `ExtractedDocument.text` is the single source of truth for downstream offsets.
3. Downstream modules (Detection, Redaction) MUST NOT alter or re-normalize this text.
4. Normalization is strictly idempotent: normalize(normalize(text)) == normalize(text).
"""

import re
import unicodedata

# Regex matching non-whitelisted control characters (retain \t, \n, \f)
RE_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# Regex matching line-trailing whitespace while preserving newlines
RE_TRAILING_WHITESPACE = re.compile(r"[ \t]+(?=\n)")


def normalize_text(text: str) -> str:
    """Normalize extracted text into canonical UTF-8 NFC representation.

    Exact Transformations Applied:
    1. Unicode Canonical Decomposition followed by Canonical Composition (NFC).
    2. Newline unification: Converts CRLF (\\r\\n) and CR (\\r) to standard LF (\\n).
    3. Stripping null bytes (\\x00) and unprintable ASCII control codes, preserving
       horizontal tabs (\\t), line feeds (\\n), and form feeds (\\f).
    4. Stripping trailing whitespace on each line before line breaks.
    5. Stripping leading and trailing whitespace from the overall string (excluding \\f).
    """
    if not text:
        return ""

    # 1. Unicode NFC
    text = unicodedata.normalize("NFC", text)

    # 2. Unify newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 3. Strip null bytes and non-whitelisted control characters
    text = text.replace("\x00", "")
    # Note: Preserve form feed (\x0c / \f), line feed (\n), tab (\t)
    text = re.sub(r"[\x01-\x08\x0b\x0e-\x1f\x7f]", "", text)

    # 4. Collapse trailing spaces on each line
    text = RE_TRAILING_WHITESPACE.sub("", text)

    return text
