# L1 Ticket Eval Corpus

Golden **Sales Cloud** and **Service Cloud** L1 helpdesk tickets used to evaluate Jataka auto-resolution against this Salesforce fixture repo.

## What these are

| Artifact | Role |
|----------|------|
| `Sales Cloud L1 Tickets-Table 1.csv` | Human-editable Sales Cloud L1 source (20 tickets) |
| `Service Cloud L1 Tickets-Table 1.csv` | Human-editable Service Cloud L1 source (20 tickets) |
| `l1-ticket-corpus.json` | Normalized machine-readable eval manifest |

These are **not** live Salesforce Case records. Live tickets remain standard Cases in the connected org. Internal workflow state lives in `one-backend` as `AutoResolutionCase`.

## Naming

| Term | Meaning |
|------|---------|
| Eval ticket (`TS-*` / `TSE-*`) | Golden L1 scenario in this folder |
| Salesforce Case | External ticket in the connected org |
| AutoResolutionCase | Internal Postgres workflow row in Jataka |

## Curriculum

Eval runs should use:

```text
curriculumId: salesforcetesting2-local-kb
```

(or the linked Brum curriculum id for this repo after GitHub backfill).

## Repo-grounded vs procedural

Each manifest entry has `repoGrounded`:

- **`true`** — answer should cite Apex/Flow/metadata in this repo (see `linkedScenarioIds` and `MCP_TEST_SCENARIOS.md`).
- **`false`** — standard Salesforce UI/process guidance; useful for L1 answer-only / escalation policy tests without requiring code citations.

## How to use

1. Prefer `l1-ticket-corpus.json` for automation (backend eval / dashboard suite).
2. Edit CSVs when authoring new tickets, then regenerate the JSON manifest.
3. Cross-check repo-grounded tickets against [MCP_TEST_SCENARIOS.md](../MCP_TEST_SCENARIOS.md) (see section **L1 ticket corpus ↔ MCP scenario cross-links**).

### Repo-grounded tickets

| Ticket | Linked MCP scenarios |
|--------|----------------------|
| `TSE-001` | `L1-KC1`, `L1-KC2`, `L1-KC3` |
| `TSE-003` | `L1-K1`, `L1-K2`, `L1-K3`, `L2-K1` |
| `TSE-009` | `L2-CM1`, `L2-CM2`, `L2-CM3` |

### API

- `GET /auto-resolution/ticket-eval/suites`
- `GET /auto-resolution/ticket-eval/tickets?suite=repo_grounded`
- `POST /auto-resolution/ticket-eval/tickets/:ticketId/run`
- `POST /auto-resolution/ticket-eval/suites/:suiteId/run`

## Related docs

- [MCP_TEST_SCENARIOS.md](../MCP_TEST_SCENARIOS.md)
- [KNOWLEDGE_CASE_ARTICLE_RUNBOOK.md](../KNOWLEDGE_CASE_ARTICLE_RUNBOOK.md)
- [KNOWLEDGE_TRANSLATION_RUNBOOK.md](../KNOWLEDGE_TRANSLATION_RUNBOOK.md)
