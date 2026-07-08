# Knowledge Translation Publishing — Consumer Support Runbook

This document mirrors the **L1 consumer issue** encoded in Apex (`KnowledgeTranslationPublishService`) for MCP validation after GitHub backfill.

## L1 issue (consumer question)

> I authored a technical troubleshooting manual in English and submitted it for translation into Spanish. Our regional team completed the Spanish translation draft, but when I try to hit **Publish** on the Spanish version, the button is greyed out. My profile has **Knowledge Manager** rights. How do I release this version?

## Ground-truth resolution

Salesforce Knowledge **isolates publishing rights per language channel and article status**.

1. **Check queue assignment** — Confirm the translated version is assigned to an explicit **Translation Queue** or validation step (not blocked only by missing profile rights).
2. **Use Draft Translations list view** — Navigate to the **Knowledge Articles** tab and switch the list view to **Draft Translations**.
3. **Submit the draft** — Select the Spanish draft and click **Submit for Publication** or **Submit for Review** to move past the translation workflow block.
4. **Language queue authorization** — If you are not a designated member of the **Spanish translation group**, a user in that language queue must authorize publication. Knowledge Manager rights alone do not bypass this.

## Repo mapping (MCP ingest)

| Concept | Artifact |
|---------|----------|
| Publish eligibility rules | `KnowledgeTranslationPublishService` |
| Spanish queue membership | `KnowledgeTranslationQueueHelper` |
| UI / API entry | `KnowledgeTranslationPublishController` |
| Translation record model | `Knowledge_Translation_Request__c` |
| Auto-assign Spanish queue on draft | `KnowledgeTranslationSubmit` flow |

## Example MCP prompts

```
L1-K: Spanish Knowledge draft Publish button greyed out — how do I release it?
L2-K: Why does Knowledge Manager profile not enable Publish on Spanish drafts?
L3-K: What depends on KnowledgeTranslationPublishService?
```
