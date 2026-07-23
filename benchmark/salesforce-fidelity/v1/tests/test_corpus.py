from __future__ import annotations

import importlib.util
import hashlib
import json
import shutil
import subprocess
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
QUERY_SPEC = importlib.util.spec_from_file_location(
    "run_query", ROOT / "tools" / "run_query.py"
)
if QUERY_SPEC is None or QUERY_SPEC.loader is None:
    raise RuntimeError("Unable to load query runner")
QUERY_RUNNER = importlib.util.module_from_spec(QUERY_SPEC)
QUERY_SPEC.loader.exec_module(QUERY_RUNNER)


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

    def test_every_case_has_a_hash_bound_execution_bundle(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text())
        self.assertEqual(20, manifest["execution_contract"]["bundle_count"])
        for entry in manifest["cases"]:
            case = json.loads((ROOT / entry["path"]).read_text())
            execution = case["execution"]
            self.assertEqual(execution, entry["execution"])
            descriptor_path = ROOT / execution["descriptor"]
            descriptor = json.loads(descriptor_path.read_text())
            self.assertEqual(entry["id"], descriptor["case_id"])
            self.assertEqual(
                execution["descriptor_sha256"],
                hashlib.sha256(descriptor_path.read_bytes()).hexdigest(),
            )
            self.assertFalse(descriptor["evidence"]["precomputed_results"])
            self.assertEqual(
                "observed_runtime_only", descriptor["evidence"]["pass_source"]
            )
            self.assertEqual(
                "jataka.ast.instructions.v1",
                descriptor["patch_contract"]["output_format"],
            )
            self.assertTrue(descriptor["patch_contract"]["raw_text_forbidden"])

    def test_apex_cases_declare_runnable_tests(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text())
        for entry in manifest["cases"]:
            case = json.loads((ROOT / entry["path"]).read_text())
            descriptor = json.loads((ROOT / case["execution"]["descriptor"]).read_text())
            test_class_name = descriptor["apex"]["test_class"]
            self.assertTrue(descriptor["apex"]["required"])
            self.assertRegex(test_class_name, r"^FidelityBenchmark\d{3}Test$")
            test_path = (
                ROOT
                / "execution"
                / entry["id"]
                / "package"
                / "main"
                / "default"
                / "classes"
                / f"{test_class_name}.cls"
            )
            self.assertTrue(test_path.is_file())
            self.assertIn(
                f"--tests {test_class_name}", descriptor["apex"]["command"]
            )

    def test_every_bundle_has_executable_seed_and_browser_harness(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text())
        for entry in manifest["cases"]:
            descriptor = json.loads(
                (ROOT / entry["execution"]["descriptor"]).read_text()
            )
            bundle = ROOT / "execution" / entry["id"]
            seed = descriptor["seed"]
            self.assertEqual(
                seed["script_sha256"],
                hashlib.sha256((bundle / seed["script"]).read_bytes()).hexdigest(),
            )
            self.assertIn("JATAKA_BINDINGS=", seed["output"]["marker"])
            self.assertEqual("/apex/FidelityBenchmark", descriptor["browser"]["route"])
            self.assertEqual(
                hashlib.sha256((ROOT / "tools" / "run_browser_case.mjs").read_bytes()).hexdigest(),
                descriptor["browser"]["driver_sha256"],
            )
            page = (
                bundle
                / "package"
                / "main"
                / "default"
                / "pages"
                / "FidelityBenchmark.page"
            ).read_text()
            self.assertIn(
                f'data-jataka-case="{entry["id"]}" data-action="run"', page
            )
            self.assertIn(
                f'data-jataka-case="{entry["id"]}" data-result=""', page
            )
            scenario = (
                bundle
                / "package"
                / "main"
                / "default"
                / "classes"
                / "FidelityBenchmarkScenario.cls"
            ).read_text()
            self.assertIn("FidelityBenchmarkScenario", scenario)
            self.assertNotIn("'PASS'", scenario)

    def test_query_runner_renders_observed_bindings_safely(self) -> None:
        rendered = QUERY_RUNNER.render(
            "SELECT Id FROM Account WHERE Id IN ${accountIds} AND Name = ${name}",
            {"accountIds": ["001000000000001", "001000000000002"], "name": "O'Reilly"},
        )
        self.assertEqual(
            "SELECT Id FROM Account WHERE Id IN "
            "('001000000000001','001000000000002') AND Name = 'O\\'Reilly'",
            rendered,
        )

    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_browser_runner_has_valid_javascript_syntax(self) -> None:
        result = subprocess.run(
            ["node", "--check", str(ROOT / "tools" / "run_browser_case.mjs")],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_event_replay_never_claims_streaming_success_locally(self) -> None:
        case = json.loads((ROOT / "cases" / "SF-FID-017.json").read_text())
        descriptor = json.loads((ROOT / case["execution"]["descriptor"]).read_text())
        replay = descriptor["event_replay"]
        self.assertEqual(["kafka", "temporal", "neo4j"], replay["external_stages"])
        self.assertTrue(replay["external_evidence_required"])
        self.assertEqual("cypher", descriptor["queries"][0]["engine"])
        self.assertIn("cannot satisfy", replay["local_adapter_scope"])

    @unittest.skipUnless(shutil.which("sf"), "Salesforce CLI is not installed")
    def test_all_execution_bundles_convert_with_salesforce_cli(self) -> None:
        result = VALIDATOR.validate_sf_conversion()
        self.assertEqual(20, result["count"])
        self.assertEqual("SF-FID-001", result["converted"][0])
        self.assertEqual("SF-FID-020", result["converted"][-1])

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
