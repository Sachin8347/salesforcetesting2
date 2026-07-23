#!/usr/bin/env python3
"""Execute a descriptor query using bindings observed from its seed command."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


def find_marker(value: Any, marker: str) -> str | None:
    if isinstance(value, str):
        index = value.find(marker)
        if index >= 0:
            return value[index + len(marker) :].splitlines()[0].strip()
    elif isinstance(value, dict):
        for child in value.values():
            found = find_marker(child, marker)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_marker(child, marker)
            if found is not None:
                return found
    return None


def soql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return f"({','.join(soql_literal(item) for item in value)})"
    escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def render(statement: str, bindings: dict[str, Any]) -> str:
    def replacement(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in bindings:
            raise ValueError(f"Seed output did not contain required binding {name!r}")
        return soql_literal(bindings[name])

    return re.sub(r"\$\{([^}]+)\}", replacement, statement)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--descriptor", default="execution.json")
    parser.add_argument("--seed-result", required=True)
    parser.add_argument("--target-org")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    descriptor = json.loads(Path(args.descriptor).read_text(encoding="utf-8"))
    query = descriptor["queries"][0]
    marker = query["bindings"]["marker"]
    seed_result = json.loads(Path(args.seed_result).read_text(encoding="utf-8"))
    encoded_bindings = find_marker(seed_result, marker)
    if encoded_bindings is None:
        raise ValueError(f"Seed result did not contain marker {marker!r}")
    bindings = json.loads(encoded_bindings)
    statement = render(query["statement"], bindings)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if query["engine"] == "cypher":
        payload = {
            "status": "EXTERNAL_EXECUTION_REQUIRED",
            "case_id": descriptor["case_id"],
            "engine": "cypher",
            "statement": statement,
            "required_stages": descriptor["event_replay"]["external_stages"],
        }
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return 2

    if not args.target_org:
        raise ValueError("--target-org is required for SOQL execution")
    command = [
        "sf",
        "data",
        "query",
        "--query",
        statement,
        "--result-format",
        "json",
        "--target-org",
        args.target_org,
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    output_path.write_text(result.stdout, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Salesforce query failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
