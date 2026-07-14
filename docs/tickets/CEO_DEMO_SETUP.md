# CEO Demo Org Setup

Use the connected Salesforce alias (`myOrg`) — do not commit auth tokens.

## Deploy fixtures

```bash
cd salesforcetesting2
sf project deploy start --source-dir force-app --target-org myOrg --wait 20
sf apex run test --class-names JatakaDemoFixtureServiceTest --target-org myOrg --result-format human --wait 15
```

## Seed situations

Anonymous Apex:

```apex
JatakaDemoFixtureService.SeedResult r = JatakaDemoFixtureService.seed('all');
System.debug(r);
```

Or REST: `POST /services/apexrest/jataka/v1/demo-fixtures` with
`{"action":"seed","scenarioId":"all"}`.

Creates / refreshes:

- `Knowledge_Translation_Request__c` named `JATAKA_DEMO_Spanish_Draft` (TSE-003)
- Case `JATAKA_DEMO_Attach_Article_Case` (TSE-001)
- Case `JATAKA_DEMO_Milestone_Lock_Case` (TSE-009)
- Account `JATAKA_DEMO_Sales_Account` when org Account automation allows it (TS-006 breadth)
- Case `JATAKA_DEMO_Missing_Entitlement_Case` (TSE-002)
- Parent Case `JATAKA_DEMO_Parent_Implementation_Case` + Child `JATAKA_DEMO_Child_IT_Subtask_Case` (TSE-007)
- Case `JATAKA_DEMO_Clone_Assignment_Case` (TSE-013)

## Dashboard

Open `/auto-resolution-demo`:

1. Choose a ticket suite (default `all_l1`) — cards are CSV ticket rows (`subject` / `issueText`)
2. **Prepare fixtures** (optional; seeds Salesforce via Apex REST for that ticket id)
3. **Run auto-resolution** (safe eval on ticket text, no external writeback)
4. Optionally **Run live writeback** when fixtures or an external record are available
5. Use **Open approval queue** (`/support-ops`) when human approval is required

Curriculum id: `salesforcetesting2-local-kb` (or the linked Brum brain for this repo).
