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
- `schema/`: JSON Schema contracts for manifests and cases.
- `corpus.lock.json`: SHA-256 digest for every governed file.
- `tools/build_corpus.py`: deterministic corpus materializer.
- `tools/validate_corpus.py`: read-only structural, semantic, and hash validator.
- `tests/test_corpus.py`: standard-library regression tests.

## Patch Contract

`patch_contract.instructions` is the only allowed model output. It is a typed
AST/metadata instruction list. Raw Apex replacement text is forbidden. The
benchmark runner must retain the original instruction payload and the
deterministic compiler output as separate hashed artifacts.

## Reproducibility

Validate without changing files:

```bash
python3 benchmark/salesforce-fidelity/v1/tools/validate_corpus.py
python3 -m unittest discover -s benchmark/salesforce-fidelity/v1/tests -v
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
  consistency, fixture line-count requirements, and immutable hashes. A live
  benchmark run must still prove first-pass compilation in a fresh scratch org.
- `SF-FID-015` deliberately models a managed-package namespace boundary. Its
  local adapter and surrounding metadata are deployable, but the full five-hop
  run requires the declared managed-package stub or licensed package.
- `SF-FID-017` is an event/metadata drift fixture rather than Apex source. Its
  acceptance test requires a live Event Monitoring/Audit Trail ingestion path.

