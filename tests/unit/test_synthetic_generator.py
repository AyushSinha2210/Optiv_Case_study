"""Unit tests for deterministic synthetic sample generator and manifest validation."""

import json
from pathlib import Path
import pytest

from demo_tools.generate_synthetic_samples import SyntheticSampleGenerator, GENERATOR_VERSION


def test_generator_determinism(tmp_path):
    """Running generator twice with the same seed produces identical file contents."""
    dir1 = tmp_path / "run1"
    dir2 = tmp_path / "run2"

    gen1 = SyntheticSampleGenerator(seed=42, output_dir=dir1)
    m1 = gen1.generate_all()

    gen2 = SyntheticSampleGenerator(seed=42, output_dir=dir2)
    m2 = gen2.generate_all()

    assert m1["fixture_count"] == m2["fixture_count"]
    assert len(m1["fixtures"]) == 20

    # Compare text contents of fixtures
    txt1 = (dir1 / "fixtures" / "01_synthetic_email.txt").read_text(encoding="utf-8")
    txt2 = (dir2 / "fixtures" / "01_synthetic_email.txt").read_text(encoding="utf-8")
    assert txt1 == txt2


def test_generator_seed_variance(tmp_path):
    """Different seeds generate different synthetic email values."""
    dir1 = tmp_path / "seed1"
    dir2 = tmp_path / "seed2"

    gen1 = SyntheticSampleGenerator(seed=101, output_dir=dir1)
    gen1.generate_all()

    gen2 = SyntheticSampleGenerator(seed=202, output_dir=dir2)
    gen2.generate_all()

    txt1 = (dir1 / "fixtures" / "01_synthetic_email.txt").read_text(encoding="utf-8")
    txt2 = (dir2 / "fixtures" / "01_synthetic_email.txt").read_text(encoding="utf-8")
    assert txt1 != txt2


def test_manifest_schema_and_path_safety(tmp_path):
    """Manifest must contain required fields and strictly safe relative paths (no traversal)."""
    gen = SyntheticSampleGenerator(seed=42, output_dir=tmp_path)
    manifest = gen.generate_all()

    assert manifest["generator_version"] == GENERATOR_VERSION
    assert manifest["seed"] == 42
    assert "privacy_notice" in manifest

    for fix in manifest["fixtures"]:
        assert "fixture_id" in fix
        assert "scenario" in fix
        assert "file_type" in fix
        assert "relative_path" in fix
        assert "expected_categories" in fix
        assert "expected_entity_count" in fix

        rel_path = fix["relative_path"]
        # No absolute paths in manifest
        assert not Path(rel_path).is_absolute()
        # No directory traversal attempts
        assert ".." not in rel_path

        # Verify physical file existence
        target = tmp_path / rel_path
        assert target.exists(), f"Fixture file not found: {target}"


def test_synthetic_values_safety_checks(tmp_path):
    """Verify that all generated email domains and phones use reserved artificial ranges."""
    gen = SyntheticSampleGenerator(seed=42, output_dir=tmp_path)
    gen.generate_all()

    phone_txt = (tmp_path / "fixtures" / "02_synthetic_phone.txt").read_text(encoding="utf-8")
    assert "(555) 01" in phone_txt  # Fictional 555-01xx range

    email_txt = (tmp_path / "fixtures" / "01_synthetic_email.txt").read_text(encoding="utf-8")
    assert "example.com" in email_txt or "example.org" in email_txt or "cadence-demo.test" in email_txt
