# MCP Consumer Support Test Matrix

This repo is a **fixture for validating Jataka MCP tools** at three consumer support levels. After linking the GitHub App and backfilling Brum, run each scenario in Cursor (or Slack/Jira integrations) and verify the expected MCP tool returns a grounded answer.

## Prerequisites

1. Install the Jataka GitHub App on this repo.
2. Link the installation to your curriculum (`POST /integrations/github/link-installation`).
3. Wait for backfill to ingest: `.cls`, `.trigger`, `.flow-meta.xml`, `.object-meta.xml`.
4. Re-run backfill or push to `main` after adding new metadata.

> **Note:** LWC files (`.js`, `.html`) are **not** ingested on GitHub backfill. UI questions in L1 rely on `brum_search` over Apex/trigger metadata only unless you extend ingestion.

---

## Support level definitions

| Level | Consumer need | Primary MCP tools | Complexity |
|-------|---------------|-------------------|------------|
| **L1** | Lookup — "what exists, where, what does it do?" | `brum_search`, `fetch_linked_metadata`, `fetch_project_rules` | Single artifact, factual |
| **L2** | Diagnose — "why is it failing / how does it behave?" | `brum_qa`, `brum_search` | Logic chain, root cause |
| **L3** | Change — "what breaks if I change X?" | `get_impact_analysis`, `fetch_linked_metadata` | Cross-component dependencies |

---

## L1 — Lookup scenarios

### Account fixtures

| # | Ask this | Expected MCP tool | Expected answer (ground truth) |
|---|----------|-------------------|--------------------------------|
| L1-1 | What does `QuickAccountController.createAccount` do? | `brum_search` or `fetch_linked_metadata` | Creates an Account with Name, Phone, and `AccountStatus__c = Pending`, then inserts. |
| L1-2 | Which Apex class is called from the `AccountBeforeInsert` trigger? | `brum_search` | `DemoAccountTriggerHandler.handleBeforeInsert` |
| L1-3 | What picklist values exist on `Account.AccountStatus__c`? | `fetch_linked_metadata` (`sub_component_type: fields`) | Pending (default), Active, Blocked |
| L1-4 | What validation rule exists on Account? | `fetch_linked_metadata` (`sub_component_type: validationRule`) | `Block_Test_Account_Names` — blocks names containing `BLOCKED` |
| L1-5 | What are the project coding standards? | `fetch_project_rules` | Returns org shadow rules / conventions from Brum |

### Knowledge translation fixtures (consumer support)

| # | Ask this | Expected MCP tool | Expected answer (ground truth) |
|---|----------|-------------------|--------------------------------|
| L1-K1 | I completed a Spanish translation draft of my English troubleshooting manual but **Publish is greyed out**. I have Knowledge Manager rights. How do I release the Spanish version? | `brum_search` or `brum_qa` | Knowledge isolates publishing per language channel/status. Check Translation Queue assignment → open **Draft Translations** list view → **Submit for Publication** or **Submit for Review** → if not in Spanish translation group, a queue member must authorize. See `KnowledgeTranslationPublishService`. |
| L1-K2 | Which class defines Knowledge translation publish eligibility rules? | `brum_search` | `KnowledgeTranslationPublishService` |
| L1-K3 | What list view should I use to find unpublished Spanish Knowledge drafts? | `brum_search` | **Draft Translations** (`LIST_VIEW_DRAFT_TRANSLATIONS` constant in `KnowledgeTranslationPublishService`) |
| L1-K4 | What picklist values exist on `Knowledge_Translation_Request__c.Translation_Status__c`? | `fetch_linked_metadata` (`sub_component_type: fields`) | Draft (default), In Translation Queue, Pending Review, Published |
| L1-K5 | Which flow assigns the Spanish Translation Group queue on draft saves? | `brum_search` | `KnowledgeTranslationSubmit` |

**Pass criteria:** Answer cites the correct class/field/ rule without hallucinating extra components.

---

## L2 — Diagnose scenarios

### Account fixtures

| # | Ask this | Expected MCP tool | Expected answer (ground truth) |
|---|----------|-------------------|--------------------------------|
| L2-1 | Why does `DemoAccountService.createDemoAccounts` fail? | `brum_qa` | Throws `IllegalArgumentException`: *Security Violation: Accounts cannot be named "Demo"* because every proposed name contains `"Demo"`. |
| L2-2 | What runs before an Account is inserted? | `brum_qa` | `AccountBeforeInsert` trigger → `DemoAccountTriggerHandler` → `AccountStatusService.applyDefaultStatus` + `markActiveWhenPhonePresent`. |
| L2-3 | Why would an Account named "ACME BLOCKED CORP" fail to save? | `brum_qa` | Validation rule `Block_Test_Account_Names` on Account (declarative), not Apex. |
| L2-4 | When does `AccountStatus__c` become Active? | `brum_qa` | (1) Before insert if Phone is populated (`AccountStatusService`), (2) After save via `AccountOnboarding` flow when Phone is not null. |
| L2-5 | How does `quickAccountWizard` create accounts? | `brum_search` | LWC calls `@AuraEnabled QuickAccountController.createAccount` — *note: LWC source may not be in graph unless ingested separately*. |

### Knowledge translation fixtures

| # | Ask this | Expected MCP tool | Expected answer (ground truth) |
|---|----------|-------------------|--------------------------------|
| L2-K1 | Why is Publish disabled even though I have Knowledge Manager rights on a Spanish draft? | `brum_qa` | Knowledge Manager ≠ Spanish queue member. Draft/In Queue status blocks direct publish; `evaluatePublishEligibility` returns `publishButtonEnabled = false` until Submit for Review and queue authorization. |
| L2-K2 | What happens when I call `submitForReview` on a Spanish draft? | `brum_qa` | Status → `Pending_Review`; `Assigned_Queue__c` defaults to **Spanish Translation Group** if blank. |
| L2-K3 | Why does `authorizePublication` throw for a Knowledge Manager? | `brum_qa` | `KnowledgeTranslationQueueHelper.isCurrentUserQueueMember('es')` is false — Spanish publish requires queue membership, not profile alone. |
| L2-K4 | What runs when a Spanish draft `Knowledge_Translation_Request__c` is saved? | `brum_qa` | `KnowledgeTranslationSubmit` flow sets `Assigned_Queue__c = Spanish Translation Group` when `Language_Code__c = es` and status is Draft. |

**Pass criteria:** Identifies the correct layer (Apex vs validation rule vs flow) and the specific line/rule causing behavior.

---

## L3 — Impact / change scenarios

### Account fixtures

| # | Ask this | Expected MCP tool | Expected dependents (minimum) |
|---|----------|-------------------|-------------------------------|
| L3-1 | What depends on `AccountStatus__c`? | `get_impact_analysis` on `AccountStatus__c` | `AccountStatusService`, `AccountStatusReportController`, `QuickAccountController`, `AccountOnboarding` flow, `DemoAccountTriggerHandler` |
| L3-2 | Impact of changing `DemoAccountTriggerHandler` | `get_impact_analysis` on `DemoAccountTriggerHandler` | `AccountBeforeInsert` trigger, indirect Account insert paths |
| L3-3 | Impact of modifying `AccountOnboarding` flow | `get_impact_analysis` on `AccountOnboarding` | Accounts with Phone set; field `AccountStatus__c` |
| L3-4 | If I remove the Demo name check in `DemoAccountService`, what's affected? | `get_impact_analysis` + `brum_qa` | Only bulk demo seed path; no trigger/flow impact |
| L3-5 | Before editing `QuickAccountController`, what should I check? | `get_impact_analysis` + `fetch_project_rules` | LWC consumer, `AccountStatus__c` assignment, sharing model (`with sharing`) |

### Knowledge translation fixtures

| # | Ask this | Expected MCP tool | Expected dependents (minimum) |
|---|----------|-------------------|-------------------------------|
| L3-K1 | What depends on `KnowledgeTranslationPublishService`? | `get_impact_analysis` on `KnowledgeTranslationPublishService` | `KnowledgeTranslationPublishController`, `KnowledgeTranslationQueueHelper` |
| L3-K2 | Impact of changing `Translation_Status__c` on `Knowledge_Translation_Request__c` | `get_impact_analysis` on `Translation_Status__c` | `KnowledgeTranslationPublishService`, `KnowledgeTranslationSubmit` flow |
| L3-K3 | Impact of modifying `KnowledgeTranslationSubmit` flow | `get_impact_analysis` on `KnowledgeTranslationSubmit` | Spanish draft records; `Assigned_Queue__c` assignment path |
| L3-K4 | Before editing Spanish queue logic, what should I check? | `get_impact_analysis` + `brum_qa` | `KnowledgeTranslationQueueHelper`, `authorizePublication`, `KnowledgeTranslationPublishController.publishAfterQueueApproval` |

**Pass criteria:** Lists real dependents from the knowledge graph; does not proceed with code changes when dependencies exist without a plan.

---

## Dependency map (ground truth)

```
Account (standard object)
├── AccountStatus__c (custom field)
├── Block_Test_Account_Names (validation rule)
│
├── AccountBeforeInsert (trigger)
│   └── DemoAccountTriggerHandler
│       └── AccountStatusService
│
├── AccountOnboarding (flow) → updates AccountStatus__c
│
├── QuickAccountController ← quickAccountWizard (LWC, may be outside graph)
├── AccountStatusReportController (SOQL on AccountStatus__c)
└── DemoAccountService (intentional L2 bug — Demo name throws)

Knowledge_Translation_Request__c (custom object — L1 consumer support fixture)
├── Language_Code__c (en_US, es)
├── Translation_Status__c (Draft → In Queue → Pending Review → Published)
├── Assigned_Queue__c
│
├── KnowledgeTranslationSubmit (flow) → assigns Spanish Translation Group on draft
│
├── KnowledgeTranslationPublishService (publish eligibility + submit/authorize)
│   └── KnowledgeTranslationQueueHelper (GroupMember check per language)
│
└── KnowledgeTranslationPublishController (@AuraEnabled MCP entry points)
```

See also: [KNOWLEDGE_TRANSLATION_RUNBOOK.md](KNOWLEDGE_TRANSLATION_RUNBOOK.md)

---

## How to run a test pass

1. Open Cursor with Jataka MCP connected to the curriculum that owns this repo.
2. For each row above, ask the question in a **fresh chat** (so `fetch_project_rules` runs cleanly).
3. Record: tool called, answer quality (pass/fail), latency.
4. After Apex edits, call `notify_code_change` with the actual changed body.

### Example Cursor prompts

```
L1: What picklist values are on Account.AccountStatus__c?
L2: Why does DemoAccountService.createDemoAccounts throw a security violation?
L3: Run impact analysis on AccountStatus__c before we rename it.

L1-K: Spanish Knowledge draft Publish is greyed out — I have Knowledge Manager rights. How do I release it?
L2-K: Why does authorizePublication fail for a Knowledge Manager on Spanish articles?
L3-K: Run impact analysis on KnowledgeTranslationPublishService before we change queue rules.
```

---

## Intentional test fixtures

| Fixture | Purpose |
|---------|---------|
| `DemoAccountService` Demo-name exception | L2 root-cause / logic-break detection |
| `Block_Test_Account_Names` validation rule | L2 declarative vs imperative distinction |
| `AccountStatus__c` shared across Apex + Flow | L3 dependency graph |
| `AccountOnboarding` flow | L1/L3 Flow metadata retrieval |
| `KnowledgeTranslationPublishService` + Spanish draft scenario | L1 consumer Knowledge publish troubleshooting |
| `KnowledgeTranslationQueueHelper` | L2 profile vs queue membership distinction |
| `Knowledge_Translation_Request__c` + `KnowledgeTranslationSubmit` flow | L3 translation workflow dependency graph |
