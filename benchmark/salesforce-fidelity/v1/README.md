# Salesforce Fidelity Benchmark v1

This directory is the frozen input corpus for Jataka's Salesforce fidelity
benchmark. It measures three independent outcomes for each of 20 cases:

1. **Blast Radius Accuracy**: every required downstream node and edge must be
   returned. One missing required dependency makes that case fail.
2. **First-Pass Compilation**: the AST transformation must compile in
   Salesforce on attempt one. Retried or text-generated patches fail.
3. **Sandbox Verification**: the scratch org must be provisioned, the patch
   applied, the declared Apex/browser/SOQL checks passed, and cleanup proven.

The aggregate release gate is at least 80% for every metric. An average cannot
hide a weak metric.

## Layout

- `manifest.json`: ordered suite metadata and strict metric thresholds.
- `cases/*.json`: immutable case contracts.
- `fixtures/`: source inputs. Runtime bugs are intentionally present, but Apex
  inputs are syntax-valid unless the case declares an external prerequisite.
- `execution/SF-FID-xxx/`: isolated source-format projects, execution
  descriptors, support metadata, named Apex tests, and per-bundle locks.
- `schema/`: JSON Schema contracts for manifests, cases, and executions.
- `corpus.lock.json`: SHA-256 digest for every governed file.
- `tools/build_corpus.py`: deterministic corpus materializer.
- `tools/validate_corpus.py`: read-only structural, semantic, and hash validator.
- `tools/run_query.py`: parses observed seed output, safely renders bind values,
  and executes the declared read-only query.
- `tools/run_browser_case.mjs`: authenticates to the generated Visualforce
  harness and captures Playwright result, trace, video, and screenshot.
- `tests/test_corpus.py`: standard-library regression tests.

## Patch Contract

`patch_contract.instructions` is the only allowed model output. It is a typed
AST/metadata instruction list. Raw Apex replacement text is forbidden. The
benchmark runner must retain the original instruction payload and the
deterministic compiler output as separate hashed artifacts.

## Execution Contract

Every `execution.json` binds the original fixture hashes and typed patch
contract to a valid Salesforce source-format project. It declares the exact
Apex test class where applicable, query engine and runtime bindings, Playwright
scenario, required evidence artifacts, and external prerequisites.

Each package contains:

- `FidelityBenchmarkScenario`, whose `seed()` method creates deterministic
  records and whose `run()` method invokes the actual case subject;
- `FidelityBenchmarkHarnessController`, a Visualforce remote-action bridge;
- `FidelityBenchmark.page`, exposing the governed `data-jataka-case`,
  `data-action`, and `data-result` selectors; and
- `scripts/seed.apex`, which emits runtime IDs after the records are committed.

The query runner reads the `JATAKA_BINDINGS=` marker from the real Salesforce
CLI seed result. It never substitutes expected IDs or checked-in pass values.

No result files are pre-populated. `pass_source` is always
`observed_runtime_only`, so local adapters or expected assertions cannot be
mistaken for successful benchmark evidence.

`SF-FID-015` uses a disclosed local `Type.forName` adapter to reproduce the
managed-package transaction effect without copying licensed code. The
production namespace boundary still requires live evidence.

`SF-FID-017` includes a deployable `Finance Analyst` Profile and
`Financial_Dashboard__c` object as the AST remediation target, plus a
deterministic payload comparison adapter. Its descriptor still requires
separate Kafka, Temporal, and Neo4j evidence; the local adapter cannot satisfy
the streaming pipeline gate.

## Reproducibility

Validate without changing files:

```bash
python3 benchmark/salesforce-fidelity/v1/tools/validate_corpus.py
python3 benchmark/salesforce-fidelity/v1/tools/validate_corpus.py --sf-convert --json
python3 -m unittest discover -s benchmark/salesforce-fidelity/v1/tests -v
```

Install the pinned browser runner dependency and validate its syntax:

```bash
cd benchmark/salesforce-fidelity/v1
npm ci --ignore-scripts
npm run check:browser-runner
```

Maintainers may intentionally regenerate the checked-in corpus and lock after
reviewing changes to `tools/build_corpus.py`:

```bash
python3 benchmark/salesforce-fidelity/v1/tools/build_corpus.py
```

Any unreviewed one-byte change to a governed file causes validation to fail.

## Declared Limitations

- Salesforce's Apex compiler is a remote service. Local validation proves JSON
  contracts, XML well-formedness, Apex delimiter/string balance, filename/class
  consistency, immutable hashes, and successful Salesforce CLI source
  conversion for all 20 packages. A live benchmark run must still prove
  first-pass compilation in a fresh scratch org.
- `SF-FID-015` deliberately models a managed-package namespace boundary. Its
  local adapter and surrounding metadata are deployable, but the full five-hop
  run requires the declared managed-package stub or licensed package.
- `SF-FID-017` is an event/metadata drift fixture rather than Apex source. Its
  acceptance test requires a live Event Monitoring/Audit Trail ingestion path.
- `SF-FID-010` requires a reachable `InvoiceGateway` Named Credential for the
  non-test Visualforce run. Its Apex test uses `HttpCalloutMock`; the browser
  harness does not manufacture a gateway success response.
