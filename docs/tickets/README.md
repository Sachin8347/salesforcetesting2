# L1 Ticket Eval Corpus

Golden **Sales Cloud** and **Service Cloud** L1 helpdesk tickets used to evaluate Jataka auto-resolution against this Salesforce fixture repo.

## What these are

| Artifact | Role |
|----------|------|
| `Sales Cloud L1 Tickets-Table 1.csv` | Sales Cloud L1 ticket table (source of truth, 20 tickets) |
| `Service Cloud L1 Tickets-Table 1.csv` | Service Cloud L1 ticket table (source of truth, 20 tickets) |

The backend loads these CSVs directly. There is **no** separate pre-fed JSON ticket deck.

These are **not** live Salesforce Case records. Live tickets remain standard Cases in the connected org. Internal workflow state lives in `one-backend` as `AutoResolutionCase`.

## Naming

| Term | Meaning |
|------|---------|
| Eval ticket (`TS-*` / `TSE-*`) | Golden L1 row in the CSV tables |
| Salesforce Case | External ticket in the connected org |
| AutoResolutionCase | Internal Postgres workflow row in Jataka |

## Curriculum

Eval runs should use:

```text
curriculumId: salesforcetesting2-local-kb
```

(or the linked Brum curriculum id for this repo after GitHub backfill).

## How to use

1. Edit the Sales/Service CSV tables when authoring tickets.
2. Backend eval / demo APIs reload from those CSVs.
3. Cross-check notable tickets against [MCP_TEST_SCENARIOS.md](../MCP_TEST_SCENARIOS.md).

### Notable tickets (docs cross-links only)

| Ticket | Linked MCP scenarios |
|--------|----------------------|
| `TSE-001` | `L1-KC1`, `L1-KC2`, `L1-KC3` |
| `TSE-003` | `L1-K1`, `L1-K2`, `L1-K3`, `L2-K1` |
| `TSE-009` | `L2-CM1`, `L2-CM2`, `L2-CM3` |

### Demo situations (CSV-driven)

Situations are CSV ticket rows:

- Suite id: `all_l1` (default), `sales_l1`, or `service_l1`
- Card fields: ticket `id`, `subject`, `issueText`, `expectedAction`

### API

- `GET /auto-resolution/ticket-eval/suites`
- `GET /auto-resolution/ticket-eval/tickets?suite=all_l1`
- `GET /auto-resolution/ticket-eval/tickets?suite=sales_l1`
- `POST /auto-resolution/ticket-eval/tickets/:ticketId/run`
- `POST /auto-resolution/ticket-eval/suites/:suiteId/run`
- `GET /auto-resolution/demo/scenarios?suite=all_l1`
- `POST /auto-resolution/demo/provision/:ticketId`
- `POST /auto-resolution/demo/run/:ticketId`

## Related docs

- [CEO_DEMO_SETUP.md](CEO_DEMO_SETUP.md)
- [MCP_TEST_SCENARIOS.md](../MCP_TEST_SCENARIOS.md)
- [KNOWLEDGE_CASE_ARTICLE_RUNBOOK.md](../KNOWLEDGE_CASE_ARTICLE_RUNBOOK.md)
- [KNOWLEDGE_TRANSLATION_RUNBOOK.md](../KNOWLEDGE_TRANSLATION_RUNBOOK.md)
