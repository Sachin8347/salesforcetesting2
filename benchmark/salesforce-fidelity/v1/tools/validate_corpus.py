#!/usr/bin/env python3
"""Read-only validator for the frozen Salesforce fidelity benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "corpus.lock.json"
MANIFEST_PATH = ROOT / "manifest.json"
CASE_ID = re.compile(r"^SF-FID-\d{3}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
FORBIDDEN_AST_KEYS = {
    "code",
    "raw_code",
    "raw_source",
    "replacement_text",
    "source",
    "text_diff",
    "unverified_text_diff",
}
EXPECTED_SHOWCASES = {
    "hidden_dependency_5_hop",
    "zero_syntax_1000_line",
    "hidden_interprocedural_o_n2",
    "bitemporal_orphan_drift",
}
EXPECTED_CATEGORIES = {
    "governor_limits",
    "data_integrity",
    "security",
    "automation",
    "async",
    "dependency_graph",
    "compiler",
    "bitemporal",
}
EXPECTED_FIXTURE_KINDS = {
    "apex_class",
    "apex_trigger",
    "apex_metadata",
    "flow_metadata",
    "profile_metadata",
    "object_metadata",
    "validation_rule_metadata",
    "audit_event",
    "github_state",
    "boundary_contract",
}
EXPECTED_DEPLOYABILITY = {
    "standalone",
    "requires_fixture_metadata",
    "requires_managed_package_stub",
    "event_replay_only",
}
EXPECTED_EXECUTION_MODES = {
    "deploy_and_test",
    "metadata_probe",
    "event_replay_adapter",
}


class CorpusError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        .encode("ascii")
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CorpusError(f"{path.relative_to(ROOT)}: invalid JSON: {exc}") from exc


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def require_keys(
    value: dict[str, Any],
    required: Iterable[str],
    allowed: Iterable[str],
    where: str,
) -> None:
    required_set = set(required)
    allowed_set = set(allowed)
    missing = sorted(required_set - value.keys())
    extra = sorted(value.keys() - allowed_set)
    if missing:
        raise CorpusError(f"{where}: missing keys {missing}")
    if extra:
        raise CorpusError(f"{where}: unsupported keys {extra}")


def assert_string(value: Any, where: str, minimum: int = 1) -> str:
    if not isinstance(value, str) or len(value) < minimum:
        raise CorpusError(f"{where}: expected string length >= {minimum}")
    return value


def validate_balanced_apex(path: Path) -> None:
    shown_path = display_path(path)
    source = path.read_text(encoding="utf-8")
    stack: list[tuple[str, int]] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    in_string = False
    in_line_comment = False
    in_block_comment = False
    escaped = False
    index = 0
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""
        if in_line_comment:
            if char == "\n":
                in_line_comment = False
            index += 1
            continue
        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
                index += 2
            else:
                index += 1
            continue
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "'":
                in_string = False
            index += 1
            continue
        if char == "/" and next_char == "/":
            in_line_comment = True
            index += 2
            continue
        if char == "/" and next_char == "*":
            in_block_comment = True
            index += 2
            continue
        if char == "'":
            in_string = True
        elif char in "([{":
            stack.append((char, index))
        elif char in ")]}":
            if not stack or stack[-1][0] != pairs[char]:
                raise CorpusError(f"{shown_path}: unbalanced {char} at {index}")
            stack.pop()
        index += 1
    if in_string or in_block_comment or stack:
        raise CorpusError(f"{shown_path}: unterminated Apex token")

    if path.suffix == ".cls":
        expected = path.stem
        declaration = re.search(
            r"\b(?:public|private|global)?\s*(?:with\s+sharing\s+|without\s+sharing\s+)?"
            r"(?:class|interface|enum)\s+([A-Za-z_][A-Za-z0-9_]*)",
            source,
        )
        if not declaration or declaration.group(1) != expected:
            raise CorpusError(
                f"{shown_path}: class declaration must match filename {expected}"
            )


def validate_ast_value(value: Any, where: str) -> None:
    if isinstance(value, dict):
        forbidden = FORBIDDEN_AST_KEYS.intersection(value)
        if forbidden:
            raise CorpusError(f"{where}: raw text key(s) forbidden: {sorted(forbidden)}")
        for key, child in value.items():
            validate_ast_value(child, f"{where}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_ast_value(child, f"{where}[{index}]")
    elif not isinstance(value, (str, int, float, bool)) and value is not None:
        raise CorpusError(f"{where}: unsupported AST value type {type(value).__name__}")


def validate_verification(value: Any, where: str) -> None:
    if not isinstance(value, dict):
        raise CorpusError(f"{where}: expected object")
    require_keys(
        value,
        ["required", "setup", "actions", "assertions", "evidence"],
        ["required", "setup", "actions", "assertions", "evidence"],
        where,
    )
    if value["required"] is not True:
        raise CorpusError(f"{where}: every verification mode must be required")
    for key in ("setup", "actions", "assertions", "evidence"):
        items = value[key]
        if not isinstance(items, list) or (key != "setup" and not items):
            raise CorpusError(f"{where}.{key}: expected non-empty list")
        if any(not isinstance(item, str) or not item for item in items):
            raise CorpusError(f"{where}.{key}: entries must be non-empty strings")


def validate_bundle_lock(bundle_root: Path, lock_path: Path, expected_digest: str) -> None:
    where = display_path(lock_path)
    lock = load_json(lock_path)
    require_keys(
        lock,
        ["schema_version", "algorithm", "bundle_sha256", "files"],
        ["schema_version", "algorithm", "bundle_sha256", "files"],
        where,
    )
    if lock["schema_version"] != "1.0.0" or lock["algorithm"] != "sha256":
        raise CorpusError(f"{where}: unsupported bundle lock format")
    actual_files = sorted(
        path.relative_to(bundle_root).as_posix()
        for path in bundle_root.rglob("*")
        if path.is_file() and path != lock_path
    )
    if sorted(lock["files"]) != actual_files:
        raise CorpusError(f"{where}.files: bundle membership drift detected")
    for relative in actual_files:
        if sha256_file(bundle_root / relative) != lock["files"][relative]:
            raise CorpusError(f"{where}: governed bundle file drift at {relative}")
    digest = hashlib.sha256(canonical_bytes(lock["files"])).hexdigest()
    if digest != lock["bundle_sha256"] or digest != expected_digest:
        raise CorpusError(f"{where}: aggregate bundle digest mismatch")


def validate_execution(
    case: dict[str, Any], summary: Any, where: str
) -> None:
    if not isinstance(summary, dict):
        raise CorpusError(f"{where}: expected object")
    keys = {
        "descriptor",
        "descriptor_sha256",
        "bundle_lock",
        "bundle_sha256",
        "mode",
        "apex_test_class",
    }
    require_keys(summary, keys, keys, where)
    case_id = case["id"]
    expected_root = ROOT / "execution" / case_id
    expected_descriptor = f"execution/{case_id}/execution.json"
    expected_lock = f"execution/{case_id}/bundle.lock.json"
    if summary["descriptor"] != expected_descriptor:
        raise CorpusError(f"{where}.descriptor: case path mismatch")
    if summary["bundle_lock"] != expected_lock:
        raise CorpusError(f"{where}.bundle_lock: case path mismatch")
    if summary["mode"] not in EXPECTED_EXECUTION_MODES:
        raise CorpusError(f"{where}.mode: unsupported execution mode")
    for key in ("descriptor_sha256", "bundle_sha256"):
        if not isinstance(summary[key], str) or not SHA256.fullmatch(summary[key]):
            raise CorpusError(f"{where}.{key}: invalid digest")

    descriptor_path = ROOT / summary["descriptor"]
    if not descriptor_path.is_file():
        raise CorpusError(f"{where}.descriptor: file not found")
    if sha256_file(descriptor_path) != summary["descriptor_sha256"]:
        raise CorpusError(f"{where}.descriptor_sha256: descriptor drift detected")
    descriptor = load_json(descriptor_path)
    descriptor_keys = {
        "schema_version",
        "case_id",
        "mode",
        "patch_contract",
        "package",
        "apex",
        "queries",
        "seed",
        "metadata_probe",
        "browser",
        "event_replay",
        "evidence",
        "prerequisites",
    }
    require_keys(descriptor, descriptor_keys, descriptor_keys, display_path(descriptor_path))
    if descriptor["schema_version"] != "1.0.0":
        raise CorpusError(f"{where}: unsupported execution descriptor version")
    if descriptor["case_id"] != case_id or descriptor["mode"] != summary["mode"]:
        raise CorpusError(f"{where}: execution identity mismatch")

    patch = descriptor["patch_contract"]
    require_keys(
        patch,
        ["output_format", "raw_text_forbidden", "sha256"],
        ["output_format", "raw_text_forbidden", "sha256"],
        f"{where}.patch_contract",
    )
    if (
        patch["output_format"] != "jataka.ast.instructions.v1"
        or patch["raw_text_forbidden"] is not True
        or patch["sha256"]
        != hashlib.sha256(canonical_bytes(case["patch_contract"])).hexdigest()
    ):
        raise CorpusError(f"{where}.patch_contract: case binding mismatch")

    package = descriptor["package"]
    require_keys(
        package,
        [
            "project_file",
            "source_root",
            "api_version",
            "fixture_bindings",
            "source_adapters",
            "generated_members",
        ],
        [
            "project_file",
            "source_root",
            "api_version",
            "fixture_bindings",
            "source_adapters",
            "generated_members",
        ],
        f"{where}.package",
    )
    if (
        package["project_file"] != "sfdx-project.json"
        or package["source_root"] != "package"
        or package["api_version"] != "60.0"
    ):
        raise CorpusError(f"{where}.package: unsupported project contract")
    project_path = expected_root / package["project_file"]
    source_root = expected_root / package["source_root"]
    if not project_path.is_file() or not source_root.is_dir():
        raise CorpusError(f"{where}.package: project files missing")

    fixtures = {item["path"]: item["sha256"] for item in case["source"]["fixtures"]}
    seen_fixtures: set[str] = set()
    for index, binding in enumerate(package["fixture_bindings"]):
        binding_where = f"{where}.package.fixture_bindings[{index}]"
        keys = {
            "fixture",
            "fixture_sha256",
            "package_member",
            "package_member_sha256",
        }
        require_keys(binding, keys, keys, binding_where)
        fixture = binding["fixture"]
        if fixture not in fixtures or binding["fixture_sha256"] != fixtures[fixture]:
            raise CorpusError(f"{binding_where}: fixture binding mismatch")
        member = expected_root / binding["package_member"]
        if (
            not member.is_file()
            or not binding["package_member"].startswith("package/main/default/")
            or sha256_file(member) != binding["package_member_sha256"]
        ):
            raise CorpusError(f"{binding_where}: package member drift")
        seen_fixtures.add(fixture)
    deployable_fixtures = {
        fixture["path"]
        for fixture in case["source"]["fixtures"]
        if fixture["kind"] not in {"audit_event", "github_state", "boundary_contract"}
    }
    if not deployable_fixtures.issubset(seen_fixtures):
        raise CorpusError(f"{where}.package.fixture_bindings: deployable fixture missing")
    generated_members = package["generated_members"]
    if not isinstance(generated_members, list) or len(generated_members) < 8:
        raise CorpusError(f"{where}.package.generated_members: harness incomplete")
    for index, generated in enumerate(generated_members):
        generated_where = f"{where}.package.generated_members[{index}]"
        require_keys(generated, ["path", "sha256"], ["path", "sha256"], generated_where)
        generated_path = expected_root / generated["path"]
        if (
            not generated["path"].startswith("package/main/default/")
            or not generated_path.is_file()
            or sha256_file(generated_path) != generated["sha256"]
        ):
            raise CorpusError(f"{generated_where}: generated artifact drift")

    for path in source_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix in {".cls", ".trigger"}:
            validate_balanced_apex(path)
        elif path.suffix == ".xml":
            try:
                ET.parse(path)
            except ET.ParseError as exc:
                raise CorpusError(f"{display_path(path)}: invalid XML: {exc}") from exc

    apex = descriptor["apex"]
    require_keys(
        apex,
        ["required", "test_class", "test_level", "command", "assertions"],
        ["required", "test_class", "test_level", "command", "assertions"],
        f"{where}.apex",
    )
    test_class = summary["apex_test_class"]
    if test_class != apex["test_class"]:
        raise CorpusError(f"{where}.apex.test_class: summary mismatch")
    if apex["required"]:
        expected_test = source_root / "main" / "default" / "classes" / f"{test_class}.cls"
        if (
            not isinstance(test_class, str)
            or not expected_test.is_file()
            or f"--tests {test_class}" not in str(apex["command"])
            or apex["test_level"] != "RunSpecifiedTests"
        ):
            raise CorpusError(f"{where}.apex: executable test declaration invalid")
    elif any(value is not None for value in (test_class, apex["command"], apex["test_level"])):
        raise CorpusError(f"{where}.apex: optional test values must be null")

    queries = descriptor["queries"]
    if not isinstance(queries, list) or not queries:
        raise CorpusError(f"{where}.queries: expected non-empty list")
    for index, query in enumerate(queries):
        query_where = f"{where}.queries[{index}]"
        keys = {
            "id",
            "engine",
            "statement",
            "bindings",
            "read_only",
            "assertions",
            "runner",
        }
        require_keys(query, keys, keys, query_where)
        if query["engine"] not in {"soql", "cypher"} or query["read_only"] is not True:
            raise CorpusError(f"{query_where}: invalid read-only query contract")
        if query["engine"] == "soql" and re.search(
            r":[A-Za-z_][A-Za-z0-9_]*", query["statement"]
        ):
            raise CorpusError(f"{query_where}: unresolved Apex bind syntax")
        bindings = query["bindings"]
        if (
            bindings.get("source") != "seed_command_stdout"
            or bindings.get("marker") != "JATAKA_BINDINGS="
            or bindings.get("renderer") != "salesforce_soql_literal_v1"
            or not isinstance(bindings.get("variables"), list)
        ):
            raise CorpusError(f"{query_where}.bindings: executable binding contract invalid")
        runner = query["runner"]
        query_runner = ROOT / "tools" / "run_query.py"
        if (
            runner.get("path") != "../../tools/run_query.py"
            or runner.get("sha256") != sha256_file(query_runner)
            or "run_query.py" not in runner.get("command", "")
        ):
            raise CorpusError(f"{query_where}.runner: governed query runner mismatch")
    if case_id == "SF-FID-017" and queries[0]["engine"] != "cypher":
        raise CorpusError(f"{where}.queries: bitemporal graph query must be Cypher")

    seed = descriptor["seed"]
    seed_keys = {
        "script",
        "script_sha256",
        "declared_bindings",
        "command",
        "output",
        "idempotency",
    }
    require_keys(seed, seed_keys, seed_keys, f"{where}.seed")
    seed_path = expected_root / seed["script"]
    if (
        seed["script"] != "scripts/seed.apex"
        or not seed_path.is_file()
        or sha256_file(seed_path) != seed["script_sha256"]
        or "sf apex run" not in seed["command"]
        or seed["output"].get("marker") != "JATAKA_BINDINGS="
        or seed["idempotency"] != "fresh_scratch_org_once_per_case"
    ):
        raise CorpusError(f"{where}.seed: executable seed contract invalid")
    required_bindings = sorted(
        {
            variable
            for query in queries
            for variable in query["bindings"]["variables"]
        }
    )
    if seed["declared_bindings"] != required_bindings:
        raise CorpusError(f"{where}.seed.declared_bindings: query binding mismatch")
    scenario_source = (
        source_root / "main" / "default" / "classes" / "FidelityBenchmarkScenario.cls"
    ).read_text(encoding="utf-8")
    for binding in required_bindings:
        if f"'{binding}'" not in scenario_source:
            raise CorpusError(
                f"{where}.seed.declared_bindings: {binding!r} not emitted by scenario"
            )

    metadata_probe = descriptor["metadata_probe"]
    if case_id == "SF-FID-007":
        if (
            not isinstance(metadata_probe, dict)
            or metadata_probe.get("required") is not True
            or metadata_probe.get("engine") != "soql"
            or metadata_probe.get("expected", {}).get("PermissionsRead") is not False
        ):
            raise CorpusError(f"{where}.metadata_probe: explicit FLS probe required")
    elif metadata_probe is not None:
        raise CorpusError(f"{where}.metadata_probe: only metadata case may declare it")

    browser = descriptor["browser"]
    browser_keys = {
        "required",
        "runner",
        "driver",
        "driver_path",
        "driver_sha256",
        "command",
        "entrypoint",
        "base_url",
        "route",
        "authentication",
        "inputs",
        "selectors",
        "scenario",
        "artifacts",
    }
    require_keys(browser, browser_keys, browser_keys, f"{where}.browser")
    if (
        browser["required"] is not True
        or browser["runner"] != "playwright"
        or browser["driver"] != "jataka.salesforce.case.v1"
        or browser["driver_path"] != "../../tools/run_browser_case.mjs"
        or browser["driver_sha256"]
        != sha256_file(ROOT / "tools" / "run_browser_case.mjs")
        or "run_browser_case.mjs" not in browser["command"]
        or browser["entrypoint"] != case_id
        or browser["route"] != "/apex/FidelityBenchmark"
        or set(browser["selectors"]) != {"action", "result"}
    ):
        raise CorpusError(f"{where}.browser: machine driver contract invalid")

    evidence = descriptor["evidence"]
    require_keys(
        evidence,
        ["precomputed_results", "required", "pass_source"],
        ["precomputed_results", "required", "pass_source"],
        f"{where}.evidence",
    )
    if (
        evidence["precomputed_results"] is not False
        or evidence["pass_source"] != "observed_runtime_only"
        or "evidence-manifest.sha256" not in evidence["required"]
    ):
        raise CorpusError(f"{where}.evidence: synthetic pass evidence is forbidden")

    replay = descriptor["event_replay"]
    if case_id == "SF-FID-017":
        if (
            not isinstance(replay, dict)
            or replay.get("external_evidence_required") is not True
            or replay.get("external_stages") != ["kafka", "temporal", "neo4j"]
        ):
            raise CorpusError(f"{where}.event_replay: external stages are mandatory")
    elif replay is not None:
        raise CorpusError(f"{where}.event_replay: only the replay case may declare it")

    validate_bundle_lock(
        expected_root, ROOT / summary["bundle_lock"], summary["bundle_sha256"]
    )


def validate_case(case: Any, path: Path, expected_id: str) -> None:
    where = path.relative_to(ROOT).as_posix()
    if not isinstance(case, dict):
        raise CorpusError(f"{where}: expected object")
    keys = [
        "schema_version",
        "id",
        "title",
        "category",
        "showcase",
        "description",
        "source",
        "blast_radius",
        "patch_contract",
        "verification",
        "execution",
        "expected_cleanup",
    ]
    require_keys(case, keys, keys, where)
    if case["schema_version"] != "1.0.0":
        raise CorpusError(f"{where}: schema_version must be 1.0.0")
    if case["id"] != expected_id or not CASE_ID.fullmatch(case["id"]):
        raise CorpusError(f"{where}: case id/path mismatch")
    assert_string(case["title"], f"{where}.title", 8)
    assert_string(case["description"], f"{where}.description", 20)
    if case["category"] not in EXPECTED_CATEGORIES:
        raise CorpusError(f"{where}.category: unsupported value")

    source = case["source"]
    require_keys(
        source,
        ["fixtures", "deployability", "entry_symbol", "minimum_lines"],
        ["fixtures", "deployability", "prerequisites", "entry_symbol", "minimum_lines"],
        f"{where}.source",
    )
    if source["deployability"] not in EXPECTED_DEPLOYABILITY:
        raise CorpusError(f"{where}.source.deployability: unsupported value")
    if not isinstance(source["fixtures"], list) or not source["fixtures"]:
        raise CorpusError(f"{where}.source.fixtures: expected non-empty list")
    total_lines = 0
    fixture_paths: set[str] = set()
    for index, fixture in enumerate(source["fixtures"]):
        fixture_where = f"{where}.source.fixtures[{index}]"
        require_keys(fixture, ["path", "sha256", "kind"], ["path", "sha256", "kind"], fixture_where)
        relative = assert_string(fixture["path"], f"{fixture_where}.path")
        if relative in fixture_paths or not relative.startswith("fixtures/"):
            raise CorpusError(f"{fixture_where}.path: duplicate or outside fixtures")
        fixture_paths.add(relative)
        if fixture["kind"] not in EXPECTED_FIXTURE_KINDS:
            raise CorpusError(f"{fixture_where}.kind: unsupported value")
        if not SHA256.fullmatch(fixture["sha256"]):
            raise CorpusError(f"{fixture_where}.sha256: invalid digest")
        fixture_path = ROOT / relative
        if not fixture_path.is_file():
            raise CorpusError(f"{fixture_where}.path: file not found")
        actual_hash = sha256_file(fixture_path)
        if actual_hash != fixture["sha256"]:
            raise CorpusError(f"{fixture_where}.sha256: fixture drift detected")
        total_lines += len(fixture_path.read_text(encoding="utf-8").splitlines())
        if fixture["kind"] in {"apex_class", "apex_trigger"}:
            validate_balanced_apex(fixture_path)
        elif fixture_path.suffix == ".xml":
            try:
                ET.parse(fixture_path)
            except ET.ParseError as exc:
                raise CorpusError(f"{relative}: invalid XML: {exc}") from exc
        elif fixture_path.suffix == ".json":
            load_json(fixture_path)
    if not isinstance(source["minimum_lines"], int) or total_lines < source["minimum_lines"]:
        raise CorpusError(
            f"{where}.source.minimum_lines: expected {source['minimum_lines']}, found {total_lines}"
        )

    blast = case["blast_radius"]
    require_keys(
        blast,
        ["root", "expected_nodes", "expected_edges", "required_hops"],
        ["root", "expected_nodes", "expected_edges", "required_hops"],
        f"{where}.blast_radius",
    )
    nodes = blast["expected_nodes"]
    edges = blast["expected_edges"]
    if not isinstance(nodes, list) or len(nodes) < 2:
        raise CorpusError(f"{where}.blast_radius.expected_nodes: expected >= 2")
    node_ids = [node.get("id") for node in nodes if isinstance(node, dict)]
    if len(node_ids) != len(nodes) or len(set(node_ids)) != len(node_ids):
        raise CorpusError(f"{where}.blast_radius.expected_nodes: invalid or duplicate ids")
    root_id = blast["root"].get("id") if isinstance(blast["root"], dict) else None
    if root_id not in node_ids:
        raise CorpusError(f"{where}.blast_radius.root: root must exist in expected_nodes")
    if not isinstance(edges, list) or not edges:
        raise CorpusError(f"{where}.blast_radius.expected_edges: expected non-empty list")
    adjacency: dict[str, set[str]] = {}
    for index, edge in enumerate(edges):
        edge_where = f"{where}.blast_radius.expected_edges[{index}]"
        require_keys(edge, ["from", "to", "kind", "evidence"], ["from", "to", "kind", "evidence"], edge_where)
        if edge["from"] not in node_ids or edge["to"] not in node_ids:
            raise CorpusError(f"{edge_where}: endpoint missing from expected_nodes")
        evidence = edge["evidence"]
        require_keys(evidence, ["fixture", "needle"], ["fixture", "needle"], f"{edge_where}.evidence")
        if evidence["fixture"] not in fixture_paths:
            raise CorpusError(f"{edge_where}.evidence.fixture: not declared in source fixtures")
        fixture_text = (ROOT / evidence["fixture"]).read_text(encoding="utf-8")
        if evidence["needle"] not in fixture_text:
            raise CorpusError(f"{edge_where}.evidence.needle: not found in fixture")
        adjacency.setdefault(edge["from"], set()).add(edge["to"])
    required_hops = blast["required_hops"]
    frontier = {root_id}
    reached = {root_id}
    longest = 0
    while frontier:
        next_frontier = {
            target
            for node in frontier
            for target in adjacency.get(node, set())
            if target not in reached
        }
        if not next_frontier:
            break
        reached.update(next_frontier)
        frontier = next_frontier
        longest += 1
    if longest < required_hops:
        raise CorpusError(
            f"{where}.blast_radius.required_hops: graph has {longest}, requires {required_hops}"
        )

    patch = case["patch_contract"]
    require_keys(
        patch,
        ["output_format", "raw_text_forbidden", "instructions"],
        ["output_format", "raw_text_forbidden", "instructions"],
        f"{where}.patch_contract",
    )
    if patch["output_format"] != "jataka.ast.instructions.v1" or patch["raw_text_forbidden"] is not True:
        raise CorpusError(f"{where}.patch_contract: AST-only contract is mandatory")
    if not isinstance(patch["instructions"], list) or not patch["instructions"]:
        raise CorpusError(f"{where}.patch_contract.instructions: expected non-empty list")
    for index, instruction in enumerate(patch["instructions"]):
        instruction_where = f"{where}.patch_contract.instructions[{index}]"
        require_keys(
            instruction,
            ["operation", "target", "node"],
            ["operation", "target", "node"],
            instruction_where,
        )
        if instruction["operation"] not in {
            "insert_before",
            "insert_after",
            "replace_node",
            "delete_node",
            "update_metadata",
        }:
            raise CorpusError(f"{instruction_where}.operation: unsupported value")
        validate_ast_value(instruction["node"], f"{instruction_where}.node")

    verification = case["verification"]
    require_keys(
        verification,
        ["apex", "browser", "soql"],
        ["apex", "browser", "soql"],
        f"{where}.verification",
    )
    for mode in ("apex", "browser", "soql"):
        validate_verification(verification[mode], f"{where}.verification.{mode}")

    validate_execution(case, case["execution"], f"{where}.execution")

    cleanup = case["expected_cleanup"]
    expected_cleanup = {
        "scratch_org_destroyed",
        "browser_context_closed",
        "active_sandbox_destroyed",
        "no_zombie_after_reaper",
    }
    require_keys(cleanup, expected_cleanup, expected_cleanup, f"{where}.expected_cleanup")
    if any(cleanup[key] is not True for key in expected_cleanup):
        raise CorpusError(f"{where}.expected_cleanup: every cleanup assertion must be true")


def validate_lock() -> None:
    lock = load_json(LOCK_PATH)
    require_keys(
        lock,
        ["schema_version", "algorithm", "corpus_sha256", "files"],
        ["schema_version", "algorithm", "corpus_sha256", "files"],
        "corpus.lock.json",
    )
    if lock["schema_version"] != "1.0.0" or lock["algorithm"] != "sha256":
        raise CorpusError("corpus.lock.json: unsupported lock format")
    files = lock["files"]
    if not isinstance(files, dict) or not files:
        raise CorpusError("corpus.lock.json.files: expected non-empty object")
    actual_governed = sorted(
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file()
        and path != LOCK_PATH
        and "node_modules" not in path.parts
        and "__pycache__" not in path.parts
        and not path.name.endswith(".pyc")
    )
    if sorted(files) != actual_governed:
        missing = sorted(set(actual_governed) - set(files))
        stale = sorted(set(files) - set(actual_governed))
        raise CorpusError(f"corpus.lock.json.files: mismatch missing={missing} stale={stale}")
    for relative in actual_governed:
        expected = files[relative]
        if not SHA256.fullmatch(expected):
            raise CorpusError(f"corpus.lock.json.files[{relative}]: invalid digest")
        actual = sha256_file(ROOT / relative)
        if actual != expected:
            raise CorpusError(f"{relative}: governed file drift detected")
    corpus_digest = hashlib.sha256(canonical_bytes(files)).hexdigest()
    if corpus_digest != lock["corpus_sha256"]:
        raise CorpusError("corpus.lock.json: aggregate corpus digest mismatch")


def validate() -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    expected_manifest_keys = {
        "schema_version",
        "benchmark_id",
        "title",
        "case_count",
        "release_gate",
        "execution_contract",
        "required_showcases",
        "cases",
    }
    require_keys(manifest, expected_manifest_keys, expected_manifest_keys, "manifest.json")
    if manifest["schema_version"] != "1.0.0":
        raise CorpusError("manifest.json: schema_version must be 1.0.0")
    if manifest["benchmark_id"] != "salesforce-fidelity-v1":
        raise CorpusError("manifest.json: unexpected benchmark_id")
    if manifest["case_count"] != 20 or len(manifest["cases"]) != 20:
        raise CorpusError("manifest.json: exactly 20 cases are required")
    gates = manifest["release_gate"]
    expected_gates = {
        "blast_radius_accuracy",
        "first_pass_compilation",
        "sandbox_verification",
    }
    require_keys(gates, expected_gates, expected_gates, "manifest.json.release_gate")
    if any(not isinstance(gates[key], (int, float)) or gates[key] < 0.8 for key in expected_gates):
        raise CorpusError("manifest.json.release_gate: every metric must be >= 0.8")
    execution_contract = manifest["execution_contract"]
    expected_execution_contract = {
        "bundle_count": 20,
        "local_source_conversion_required": True,
        "runtime_evidence_must_be_observed": True,
        "synthetic_pass_results_forbidden": True,
    }
    if execution_contract != expected_execution_contract:
        raise CorpusError("manifest.json.execution_contract: strict contract required")
    if set(manifest["required_showcases"]) != EXPECTED_SHOWCASES:
        raise CorpusError("manifest.json.required_showcases: all four showcases are mandatory")

    ids: list[str] = []
    showcases: set[str] = set()
    category_counts: dict[str, int] = {}
    for entry in manifest["cases"]:
        require_keys(
            entry,
            ["id", "path", "sha256", "execution"],
            ["id", "path", "sha256", "execution"],
            "manifest.json.cases[]",
        )
        case_id = entry["id"]
        if not CASE_ID.fullmatch(case_id):
            raise CorpusError(f"manifest.json: invalid case id {case_id!r}")
        if case_id in ids:
            raise CorpusError(f"manifest.json: duplicate case id {case_id}")
        ids.append(case_id)
        expected_path = f"cases/{case_id}.json"
        if entry["path"] != expected_path:
            raise CorpusError(f"manifest.json: path mismatch for {case_id}")
        case_path = ROOT / expected_path
        if not case_path.is_file() or sha256_file(case_path) != entry["sha256"]:
            raise CorpusError(f"manifest.json: case hash mismatch for {case_id}")
        case = load_json(case_path)
        validate_case(case, case_path, case_id)
        if entry["execution"] != case["execution"]:
            raise CorpusError(f"manifest.json: execution summary mismatch for {case_id}")
        showcases.add(case["showcase"])
        category_counts[case["category"]] = category_counts.get(case["category"], 0) + 1
    if ids != [f"SF-FID-{index:03d}" for index in range(1, 21)]:
        raise CorpusError("manifest.json: cases must be ordered SF-FID-001 through SF-FID-020")
    if not EXPECTED_SHOWCASES.issubset(showcases):
        raise CorpusError("manifest.json: showcase case missing")
    if len(category_counts) < 6:
        raise CorpusError("manifest.json: corpus must cover at least six categories")

    validate_lock()
    return {
        "benchmark_id": manifest["benchmark_id"],
        "cases": len(ids),
        "categories": category_counts,
        "showcases": sorted(showcases - {"internal"}),
        "corpus_sha256": load_json(LOCK_PATH)["corpus_sha256"],
        "status": "PASS",
    }


def validate_sf_conversion() -> dict[str, Any]:
    converted: list[str] = []
    for case_id in (f"SF-FID-{index:03d}" for index in range(1, 21)):
        bundle_root = ROOT / "execution" / case_id
        with tempfile.TemporaryDirectory(prefix=f"{case_id.lower()}-") as directory:
            output = Path(directory) / "metadata"
            command = [
                "sf",
                "project",
                "convert",
                "source",
                "--root-dir",
                "package",
                "--output-dir",
                str(output),
            ]
            result = subprocess.run(
                command,
                cwd=bundle_root,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                detail = (result.stderr or result.stdout).strip()
                raise CorpusError(f"{case_id}: Salesforce source conversion failed: {detail}")
            package_xml = output / "package.xml"
            if not package_xml.is_file():
                raise CorpusError(f"{case_id}: conversion did not produce package.xml")
            converted.append(case_id)
    return {"converted": converted, "count": len(converted)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    parser.add_argument(
        "--sf-convert",
        action="store_true",
        help="also convert every isolated bundle with the local Salesforce CLI",
    )
    args = parser.parse_args()
    try:
        result = validate()
        if args.sf_convert:
            result["source_conversion"] = validate_sf_conversion()
    except CorpusError as exc:
        if args.json:
            print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
        else:
            print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            f"PASS: {result['cases']} cases; corpus_sha256={result['corpus_sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
