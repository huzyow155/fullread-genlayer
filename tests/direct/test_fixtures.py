import unittest
import json
import os
from tests.direct.test_pure_helpers import (
    _sha, _norm, _chunks, _grounded, _parse, _clean_chunk, _reduce, _same_decision, _strip_tags
)
from tests.direct.test_pipeline_and_validator import MockResponse, run_simulated_analyze

class TestFixturesExecution(unittest.TestCase):
    def setUp(self):
        self.items = [
            {"id": "refund", "question": "Clear refund policy present", "severity": "BLOCKER", "polarity": "MUST_HAVE"},
            {"id": "auto_renew", "question": "Auto renewal without prior notice", "severity": "BLOCKER", "polarity": "MUST_NOT_HAVE"}
        ]
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), "..", "fixtures")

    def _smart_mock_llm(self, prompt, chunk_idx, chunk_text):
        results = {
            "refund": {"status": "ABSENT", "quote": ""},
            "auto_renew": {"status": "ABSENT", "quote": ""}
        }
        if "mandatory 30-day refund policy" in chunk_text:
            results["refund"] = {"status": "PRESENT", "quote": "mandatory 30-day refund policy for all purchases"}
        if "auto-renew without notice" in chunk_text:
            results["auto_renew"] = {"status": "PRESENT", "quote": "auto-renew without notice at the end of each billing cycle"}
        return json.dumps({"results": results})

    def test_compliant_fixture_yields_PASS(self):
        path = os.path.join(self.fixtures_dir, "compliant.md")
        content = open(path, "r", encoding="utf-8").read()
        res, chunks = run_simulated_analyze(
            "http://test.local/compliant.md",
            self.items,
            max_chunks=3,
            mock_web_get=lambda u: MockResponse(200, content),
            mock_exec_prompt=self._smart_mock_llm
        )
        self.assertEqual(len(chunks), 3)
        self.assertEqual(res["coverage_bp"], 10000)
        self.assertEqual(res["status_by_item"]["refund"], "SATISFIED")
        self.assertEqual(res["status_by_item"]["auto_renew"], "CLEAR")
        self.assertEqual(res["outcome"], "PASS")

    def test_violation_in_first_chunk_yields_FAIL(self):
        path = os.path.join(self.fixtures_dir, "violation_in_first_chunk.md")
        content = open(path, "r", encoding="utf-8").read()
        res, chunks = run_simulated_analyze(
            "http://test.local/violation_in_first_chunk.md",
            self.items,
            max_chunks=3,
            mock_web_get=lambda u: MockResponse(200, content),
            mock_exec_prompt=self._smart_mock_llm
        )
        self.assertEqual(len(chunks), 3)
        self.assertEqual(res["coverage_bp"], 10000)
        self.assertEqual(res["status_by_item"]["refund"], "SATISFIED")
        self.assertEqual(res["status_by_item"]["auto_renew"], "VIOLATED")
        self.assertEqual(res["outcome"], "FAIL")

    def test_violation_in_last_chunk_yields_FAIL_on_full_and_clear_on_single_chunk(self):
        path = os.path.join(self.fixtures_dir, "violation_in_last_chunk.md")
        content = open(path, "r", encoding="utf-8").read()

        # Reading only chunk 1 (max_chunks=1): misses the buried trap clause!
        res_single, chunks_single = run_simulated_analyze(
            "http://test.local/violation_in_last_chunk.md",
            self.items,
            max_chunks=1,
            mock_web_get=lambda u: MockResponse(200, content),
            mock_exec_prompt=self._smart_mock_llm
        )
        self.assertEqual(len(chunks_single), 1)
        self.assertLess(res_single["coverage_bp"], 10000)
        # Buried violation was not in chunk 1, so status is UNRESOLVED due to partial coverage
        self.assertEqual(res_single["status_by_item"]["auto_renew"], "UNRESOLVED")
        self.assertNotEqual(res_single["outcome"], "FAIL")

        # FullRead reading all 3 chunks: catches the buried clause in chunk 3 and FAILS!
        res_full, chunks_full = run_simulated_analyze(
            "http://test.local/violation_in_last_chunk.md",
            self.items,
            max_chunks=3,
            mock_web_get=lambda u: MockResponse(200, content),
            mock_exec_prompt=self._smart_mock_llm
        )
        self.assertEqual(len(chunks_full), 3)
        self.assertEqual(res_full["coverage_bp"], 10000)
        self.assertEqual(res_full["status_by_item"]["auto_renew"], "VIOLATED")
        self.assertEqual(res_full["outcome"], "FAIL")

if __name__ == "__main__":
    unittest.main()
