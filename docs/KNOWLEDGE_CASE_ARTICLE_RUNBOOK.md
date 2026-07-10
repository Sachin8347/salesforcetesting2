# Knowledge Case Article — Consumer Support Runbook

This document mirrors the **L1 consumer issue** encoded in Apex (`KnowledgeCaseResolutionService`) for MCP validation after GitHub backfill.

## L1 issue (consumer question)

> I am working on an intricate technical issue. I found an internal Knowledge Article that perfectly explains the resolution steps. How do I attach this article directly to the active Case record layout so it is tracked in our resolution metrics, and how can I send its text content straight to the customer's email box via the console?

## Ground-truth resolution

1. **Attach for metrics** — Open the active Case in Service Console. Use the **Knowledge / Articles** component or the **Case Articles** related list to associate the article. That CaseArticle link is what feeds resolution / Knowledge usage metrics.
2. **Email article text** — Open the console **Email** composer on the Case. Use **Insert Knowledge** / **Share Article** (or paste the customer-visible body) so the content is included in the outbound email, then send.
3. **Visibility guardrail** — Internal App–only articles must not be emailed to customers. Publish or share to a customer-visible channel first. You can still attach the article to the Case for internal metrics.
4. **Imperative vs how-to** — “How do I attach/send…?” is L1 answer-only. “Attach article X to Case Y and send it now” is a DATA_ACTION requiring human approval.

## Repo mapping (MCP ingest)

| Concept | Artifact |
|---------|----------|
| Attach + email how-to rules | `KnowledgeCaseResolutionService` |
| AuraEnabled MCP entry | `KnowledgeCaseResolutionController` |
| Case Articles related list constant | `RELATED_LIST_CASE_ARTICLES` |
| Insert Knowledge action | `ACTION_INSERT_KNOWLEDGE` |
| Internal-only email block | `BLOCK_INTERNAL_ONLY` |

## Example MCP prompts

```
L1-KC: How do I attach a Knowledge article to a Case and email its content from the console?
L2-KC: Why is Insert Knowledge unavailable for an internal article on a Case email?
L3-KC: What depends on KnowledgeCaseResolutionService?
```
