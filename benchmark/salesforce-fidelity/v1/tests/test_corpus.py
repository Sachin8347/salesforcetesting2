from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_corpus", ROOT / "tools" / "validate_corpus.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load corpus validator")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class CorpusTests(unittest.TestCase):
    def test_frozen_corpus_is_valid(self) -> None:
        result = VALIDATOR.validate()
        self.assertEqual("PASS", result["status"])
        self.assertEqual(20, result["cases"])

    def test_every_case_requires_all_three_runtime_checks(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text())
        for entry in manifest["cases"]:
            case = json.loads((ROOT / entry["path"]).read_text())
            self.assertEqual({"apex", "browser", "soql"}, set(case["verification"]))
            self.assertTrue(all(mode["required"] for mode in case["verification"].values()))

    def test_ast_contract_rejects_raw_source_keys(self) -> None:
        with self.assertRaisesRegex(VALIDATOR.CorpusError, "raw text key"):
            VALIDATOR.validate_ast_value(
                {"type": "Statement", "raw_source": "return null;"},
                "test",
            )

    def test_apex_balance_check_rejects_missing_brace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Broken.cls"
            path.write_text("public class Broken { public void run() { }\n")
            with self.assertRaisesRegex(VALIDATOR.CorpusError, "unterminated Apex token"):
                VALIDATOR.validate_balanced_apex(path)

    def test_showcase_line_and_hop_requirements(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text())
        showcases = {}
        for entry in manifest["cases"]:
            case = json.loads((ROOT / entry["path"]).read_text())
            showcases[case["showcase"]] = case
        self.assertGreaterEqual(
            showcases["hidden_dependency_5_hop"]["blast_radius"]["required_hops"], 5
        )
        self.assertGreaterEqual(
            showcases["zero_syntax_1000_line"]["source"]["minimum_lines"], 1000
        )
        self.assertIn("o_n2", showcases["hidden_interprocedural_o_n2"]["showcase"])
        self.assertEqual(
            "event_replay_only",
            showcases["bitemporal_orphan_drift"]["source"]["deployability"],
        )


if __name__ == "__main__":
    unittest.main()

