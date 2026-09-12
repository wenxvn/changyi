from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from backend.app.infrastructure.data.import_pipeline import (
    assert_raw_not_used_by_application,
    quality_gate,
    read_raw_metadata,
    write_raw_snapshot,
)


class ImportPipelineTests(TestCase):
    def test_raw_snapshot_is_readonly_metadata_and_not_application_source(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_raw_snapshot(
                dataset="hospitals_demo",
                source_url="https://example.invalid/hospitals",
                provider="demo",
                payload={"records": [{"id": 1, "name": "示例医院"}]},
                license_status="demo-only",
                root=root,
            )
            meta = read_raw_metadata("hospitals_demo", root=root)
            self.assertTrue(path.is_file())
            self.assertTrue(meta["readonly"])
            self.assertTrue(meta["application_layer_must_not_read"])
            self.assertEqual(meta["source_url"], "https://example.invalid/hospitals")
            self.assertEqual(len(meta["sha256"]), 64)

    def test_quality_gate_requires_source_license_and_timestamp_for_rankable(self):
        verified = quality_gate(
            schema_valid=True,
            source_url="https://example.invalid/bus",
            license_status="CC-BY-4.0",
            captured_at="2026-09-12T00:00:00+00:00",
        )
        provisional = quality_gate(
            schema_valid=True,
            source_url=None,
            license_status="not_recorded",
            captured_at=None,
        )
        invalid = quality_gate(
            schema_valid=False,
            source_url=None,
            license_status="not_recorded",
            captured_at=None,
        )

        self.assertEqual(verified.verification_status, "VERIFIED")
        self.assertTrue(verified.rankable)
        self.assertTrue(verified.displayable)
        self.assertEqual(provisional.verification_status, "PROVISIONAL")
        self.assertFalse(provisional.rankable)
        self.assertTrue(provisional.displayable)
        self.assertEqual(invalid.verification_status, "INVALID")
        self.assertFalse(invalid.displayable)
        self.assertFalse(invalid.rankable)

    def test_application_packages_do_not_read_raw_snapshots(self):
        assert_raw_not_used_by_application(Path.cwd())
