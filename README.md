# salesforcetesting2

Demo Salesforce project used to **test Jataka MCP consumer support** at L1, L2, and L3.

## What's in this repo

- **Apex:** `QuickAccountController`, `DemoAccountService`, `AccountStatusService`, `AccountStatusReportController`, trigger handler
- **Knowledge (L1 consumer support):** `KnowledgeTranslationPublishService`, `KnowledgeTranslationQueueHelper`, `KnowledgeTranslationPublishController`
- **Trigger:** `AccountBeforeInsert` on Account
- **Metadata:** `AccountStatus__c` picklist, Account validation rule, `Knowledge_Translation_Request__c`, `AccountOnboarding` + `KnowledgeTranslationSubmit` flows
- **LWC:** `quickAccountWizard` (UI smoke test; not in default GitHub backfill)

## MCP test guide

See **[docs/MCP_TEST_SCENARIOS.md](docs/MCP_TEST_SCENARIOS.md)** for the full question matrix, expected tools, and pass criteria.

Quick reference:

| Level | Example question |
|-------|------------------|
| L1 | What does `QuickAccountController` do? |
| L1-K | Spanish Knowledge draft Publish greyed out — how do I release it? |
| L2 | Why does `DemoAccountService` fail on demo accounts? |
| L2-K | Why doesn't Knowledge Manager rights enable Publish on Spanish drafts? |
| L3 | What depends on `AccountStatus__c`? |
| L3-K | What depends on `KnowledgeTranslationPublishService`? |

## Setup

1. Connect this repo via the Jataka GitHub App.
2. Link installation to your curriculum and backfill `main`.
3. Run scenarios from the test matrix in Cursor with MCP enabled.
