#!/usr/bin/env python3
"""Deterministically materialize and freeze the Salesforce fidelity corpus."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
API_VERSION = "60.0"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def write_text(relative: str, value: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_json(relative: str, value: Any) -> None:
    write_text(relative, json.dumps(value, indent=2, sort_keys=True))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apex_meta(status: str = "Active") -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>{API_VERSION}</apiVersion>
    <status>{status}</status>
</ApexClass>"""


def trigger_meta() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ApexTrigger xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>{API_VERSION}</apiVersion>
    <status>Active</status>
</ApexTrigger>"""


def ast_instruction(
    operation: str,
    symbol: str,
    node_type: str,
    selector: str,
    node: dict[str, Any],
) -> dict[str, Any]:
    return {
        "operation": operation,
        "target": {
            "symbol": symbol,
            "node_type": node_type,
            "selector": selector,
        },
        "node": node,
    }


def method_call(receiver: str, method: str, arguments: list[Any]) -> dict[str, Any]:
    return {
        "type": "MethodCall",
        "receiver": {"type": "Identifier", "name": receiver},
        "method": method,
        "arguments": arguments,
    }


def metadata_update(
    symbol: str, selector: str, metadata_type: str, member: str, path: str, value: Any
) -> dict[str, Any]:
    return ast_instruction(
        "update_metadata",
        symbol,
        "MetadataNode",
        selector,
        {
            "type": "MetadataMutation",
            "metadata_type": metadata_type,
            "member": member,
            "path": path,
            "value": value,
        },
    )


def generic_verification(
    title: str,
    apex_assertion: str,
    browser_assertion: str,
    soql_query: str,
    soql_assertion: str,
) -> dict[str, Any]:
    return {
        "apex": {
            "required": True,
            "setup": [f"Create isolated records for {title} with SeeAllData=false."],
            "actions": [
                "Deploy the deterministic compiler output on attempt one.",
                "Run the named benchmark Apex test with synchronous result collection.",
            ],
            "assertions": [
                apex_assertion,
                "The deployment record reports compilation_attempt=1 and compile_success=true.",
            ],
            "evidence": [
                "Salesforce deploy result JSON",
                "Apex test result JSON",
                "compiler input/output SHA-256",
            ],
        },
        "browser": {
            "required": True,
            "setup": ["Create a least-privilege affected user and seed the declared records."],
            "actions": [
                "Open the affected Lightning record page as the affected user.",
                "Perform the user action that reproduced the original failure.",
            ],
            "assertions": [
                browser_assertion,
                "The Playwright trace contains no uncaught page or console error.",
            ],
            "evidence": [
                "Playwright trace.zip",
                "recorded video",
                "final-state screenshot",
            ],
        },
        "soql": {
            "required": True,
            "setup": ["Capture record identifiers created by the Apex test-data factory."],
            "actions": [f"Execute read-only SOQL: {soql_query}"],
            "assertions": [soql_assertion],
            "evidence": ["SOQL result JSON", "query timestamp and target-org alias"],
        },
    }


def graph_node(node_id: str, node_type: str) -> dict[str, str]:
    return {"id": node_id, "type": node_type}


def source_path(case_id: int | str, filename: str) -> str:
    normalized = f"SF-FID-{case_id:03d}" if isinstance(case_id, int) else case_id
    return f"fixtures/{normalized}/{filename}"


def class_case(
    number: int,
    title: str,
    category: str,
    description: str,
    class_name: str,
    apex: str,
    nodes: list[tuple[str, str]],
    edges: list[tuple[str, str, str, str]],
    patch: list[dict[str, Any]],
    apex_assertion: str,
    browser_assertion: str,
    soql_query: str,
    soql_assertion: str,
    *,
    showcase: str = "internal",
    required_hops: int = 2,
    deployability: str = "standalone",
    prerequisites: list[str] | None = None,
    minimum_lines: int = 10,
    extra_fixtures: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    case_id = f"SF-FID-{number:03d}"
    fixture = source_path(case_id, f"{class_name}.cls")
    write_text(fixture, apex)
    meta = source_path(case_id, f"{class_name}.cls-meta.xml")
    write_text(meta, apex_meta())
    fixture_entries = [
        {"path": fixture, "sha256": sha256_file(ROOT / fixture), "kind": "apex_class"},
        {"path": meta, "sha256": sha256_file(ROOT / meta), "kind": "apex_metadata"},
    ]
    if extra_fixtures:
        for extra in extra_fixtures:
            fixture_entries.append(
                {
                    "path": extra["path"],
                    "sha256": sha256_file(ROOT / extra["path"]),
                    "kind": extra["kind"],
                }
            )
    return {
        "schema_version": "1.0.0",
        "id": case_id,
        "title": title,
        "category": category,
        "showcase": showcase,
        "description": description,
        "source": {
            "fixtures": fixture_entries,
            "deployability": deployability,
            "prerequisites": prerequisites or [],
            "entry_symbol": class_name,
            "minimum_lines": minimum_lines,
        },
        "blast_radius": {
            "root": graph_node(*nodes[0]),
            "expected_nodes": [graph_node(*node) for node in nodes],
            "expected_edges": [
                {
                    "from": edge_from,
                    "to": edge_to,
                    "kind": kind,
                    "evidence": {"fixture": fixture, "needle": needle},
                }
                for edge_from, edge_to, kind, needle in edges
            ],
            "required_hops": required_hops,
        },
        "patch_contract": {
            "output_format": "jataka.ast.instructions.v1",
            "raw_text_forbidden": True,
            "instructions": patch,
        },
        "verification": generic_verification(
            title,
            apex_assertion,
            browser_assertion,
            soql_query,
            soql_assertion,
        ),
        "expected_cleanup": {
            "scratch_org_destroyed": True,
            "browser_context_closed": True,
            "active_sandbox_destroyed": True,
            "no_zombie_after_reaper": True,
        },
    }


def large_class() -> str:
    lines = [
        "public with sharing class FidelityLargeInvoiceService {",
        "    public static Map<Id, Decimal> calculateTotals(List<Account> accounts) {",
        "        Map<Id, Decimal> totals = new Map<Id, Decimal>();",
        "        for (Account accountRecord : accounts) {",
        "            Decimal total = 0;",
        "            for (Opportunity item : [",
        "                SELECT Amount FROM Opportunity WHERE AccountId = :accountRecord.Id",
        "            ]) {",
        "                total += item.Amount == null ? 0 : item.Amount;",
        "            }",
        "            totals.put(accountRecord.Id, total);",
        "        }",
        "        return totals;",
        "    }",
        "",
    ]
    for index in range(1, 126):
        lines.extend(
            [
                f"    private static Decimal normalize{index:03d}(Decimal value) {{",
                "        if (value == null) {",
                "            return 0;",
                "        }",
                f"        Decimal scale = {index};",
                "        Decimal normalized = value.setScale(2);",
                "        return normalized + scale - scale;",
                "    }",
                "",
            ]
        )
    lines.extend(
        [
            "    public static Decimal normalizeForDisplay(Decimal value) {",
            "        return normalize001(value);",
            "    }",
            "}",
        ]
    )
    return "\n".join(lines)


def build_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    cases.append(
        class_case(
            1,
            "SOQL query inside account loop",
            "governor_limits",
            "A publication-scale Account batch issues one Contact query per record and exceeds the synchronous query governor limit.",
            "FidelityDirectQueryService",
            """public with sharing class FidelityDirectQueryService {
    public static Map<Id, Integer> contactCounts(List<Account> accounts) {
        Map<Id, Integer> result = new Map<Id, Integer>();
        for (Account accountRecord : accounts) {
            List<Contact> contacts = [
                SELECT Id, AccountId FROM Contact WHERE AccountId = :accountRecord.Id
            ];
            result.put(accountRecord.Id, contacts.size());
        }
        return result;
    }
}""",
            [
                ("FidelityDirectQueryService.contactCounts", "ApexMethod"),
                ("Account", "Object"),
                ("Contact.AccountId", "CustomField"),
            ],
            [
                ("FidelityDirectQueryService.contactCounts", "Account", "ITERATES", "for (Account accountRecord : accounts)"),
                ("Account", "Contact.AccountId", "QUERIES_BY", "WHERE AccountId = :accountRecord.Id"),
            ],
            [
                ast_instruction(
                    "replace_node",
                    "FidelityDirectQueryService.contactCounts",
                    "ForStatement",
                    "loop:accountRecord",
                    {
                        "type": "BulkQueryPlan",
                        "collect": {"type": "SetExpression", "sobject": "Account", "field": "Id"},
                        "query": {
                            "type": "SoqlQuery",
                            "sobject": "Contact",
                            "fields": ["Id", "AccountId"],
                            "predicate": {"field": "AccountId", "operator": "IN", "binding": "accountIds"},
                        },
                        "group_by": "AccountId",
                    },
                )
            ],
            "Two hundred Accounts complete with one Contact query and correct zero counts.",
            "The Account contact-count panel renders the expected count without a save error.",
            "SELECT AccountId, COUNT(Id) total FROM Contact WHERE AccountId IN :accountIds GROUP BY AccountId",
            "Returned grouped counts equal the Apex result for every seeded Account.",
        )
    )

    cases.append(
        class_case(
            2,
            "DML statement inside opportunity loop",
            "governor_limits",
            "An opportunity stage update performs one database update per row and exceeds the DML statement governor limit.",
            "FidelityDmlLoopService",
            """public with sharing class FidelityDmlLoopService {
    public static void closeWon(List<Opportunity> opportunities) {
        for (Opportunity opportunityRecord : opportunities) {
            opportunityRecord.StageName = 'Closed Won';
            opportunityRecord.CloseDate = Date.today();
            update opportunityRecord;
        }
    }
}""",
            [
                ("FidelityDmlLoopService.closeWon", "ApexMethod"),
                ("Opportunity", "Object"),
                ("Opportunity.StageName", "CustomField"),
            ],
            [
                ("FidelityDmlLoopService.closeWon", "Opportunity", "MUTATES", "update opportunityRecord"),
                ("Opportunity", "Opportunity.StageName", "WRITES_FIELD", "StageName = 'Closed Won'"),
            ],
            [
                ast_instruction(
                    "replace_node",
                    "FidelityDmlLoopService.closeWon",
                    "DmlStatement",
                    "update:inside:loop",
                    {
                        "type": "DeferredDml",
                        "collection": "opportunities",
                        "operation": "UPDATE",
                        "placement": "AFTER_LOOP",
                    },
                )
            ],
            "Two hundred Opportunities are closed using exactly one DML statement.",
            "The bulk close action shows 200 successful records and no governor-limit toast.",
            "SELECT Id, StageName, CloseDate FROM Opportunity WHERE Id IN :opportunityIds",
            "Every row is Closed Won with today's close date.",
        )
    )

    cases.append(
        class_case(
            3,
            "Hidden interprocedural quadratic CPU path",
            "governor_limits",
            "A trigger-facing method calls through three helpers before a nested scan, hiding O(n^2) work from basic loop linters.",
            "FidelityHiddenQuadraticService",
            """public with sharing class FidelityHiddenQuadraticService {
    public static Map<Id, Integer> scoreAccounts(List<Account> accounts, List<Contact> contacts) {
        return dispatch(accounts, contacts);
    }
    private static Map<Id, Integer> dispatch(List<Account> accounts, List<Contact> contacts) {
        return calculate(accounts, contacts);
    }
    private static Map<Id, Integer> calculate(List<Account> accounts, List<Contact> contacts) {
        Map<Id, Integer> scores = new Map<Id, Integer>();
        for (Account accountRecord : accounts) {
            scores.put(accountRecord.Id, countMatches(accountRecord.Id, contacts));
        }
        return scores;
    }
    private static Integer countMatches(Id accountId, List<Contact> contacts) {
        Integer countValue = 0;
        for (Contact contactRecord : contacts) {
            if (contactRecord.AccountId == accountId) {
                countValue++;
            }
        }
        return countValue;
    }
}""",
            [
                ("FidelityHiddenQuadraticService.scoreAccounts", "ApexMethod"),
                ("FidelityHiddenQuadraticService.dispatch", "ApexMethod"),
                ("FidelityHiddenQuadraticService.calculate", "ApexMethod"),
                ("FidelityHiddenQuadraticService.countMatches", "ApexMethod"),
                ("Contact.AccountId", "CustomField"),
            ],
            [
                ("FidelityHiddenQuadraticService.scoreAccounts", "FidelityHiddenQuadraticService.dispatch", "CALLS", "return dispatch(accounts, contacts)"),
                ("FidelityHiddenQuadraticService.dispatch", "FidelityHiddenQuadraticService.calculate", "CALLS", "return calculate(accounts, contacts)"),
                ("FidelityHiddenQuadraticService.calculate", "FidelityHiddenQuadraticService.countMatches", "CALLS_IN_LOOP", "countMatches(accountRecord.Id, contacts)"),
                ("FidelityHiddenQuadraticService.countMatches", "Contact.AccountId", "READS_IN_LOOP", "contactRecord.AccountId == accountId"),
            ],
            [
                ast_instruction(
                    "replace_node",
                    "FidelityHiddenQuadraticService.calculate",
                    "ForStatement",
                    "loop:accounts",
                    {
                        "type": "LinearIndexPlan",
                        "index": {
                            "type": "MapAccumulator",
                            "key_field": "Contact.AccountId",
                            "value": "COUNT",
                            "input": "contacts",
                        },
                        "lookup": {"map": "contactCountsByAccount", "key_field": "Account.Id", "default": 0},
                    },
                )
            ],
            "Ten thousand Accounts and Contacts finish under the configured CPU ceiling with linear operation growth.",
            "The profile run displays projected complexity O(n) and permits the pull request.",
            "SELECT AccountId, COUNT(Id) total FROM Contact WHERE AccountId IN :accountIds GROUP BY AccountId",
            "Grouped database counts equal all indexed Apex counts.",
            showcase="hidden_interprocedural_o_n2",
            required_hops=4,
            minimum_lines=20,
        )
    )

    cases.append(
        class_case(
            4,
            "Recursive account trigger handler",
            "automation",
            "An after-update handler writes the triggering Accounts again without a transaction guard, recursively re-entering automation.",
            "FidelityRecursiveAccountHandler",
            """public with sharing class FidelityRecursiveAccountHandler {
    public static void afterUpdate(List<Account> records) {
        List<Account> pending = new List<Account>();
        for (Account accountRecord : records) {
            pending.add(new Account(Id = accountRecord.Id, Description = 'Normalized'));
        }
        if (!pending.isEmpty()) {
            update pending;
        }
    }
}""",
            [
                ("AccountAfterUpdate", "ApexTrigger"),
                ("FidelityRecursiveAccountHandler.afterUpdate", "ApexMethod"),
                ("Account", "Object"),
            ],
            [
                ("AccountAfterUpdate", "FidelityRecursiveAccountHandler.afterUpdate", "CALLS", "public static void afterUpdate"),
                ("FidelityRecursiveAccountHandler.afterUpdate", "Account", "REENTERS_TRIGGER", "update pending"),
            ],
            [
                ast_instruction(
                    "insert_before",
                    "FidelityRecursiveAccountHandler.afterUpdate",
                    "MethodBody",
                    "first_statement",
                    {
                        "type": "TransactionGuard",
                        "key": "FidelityRecursiveAccountHandler.afterUpdate",
                        "on_reentry": {"type": "ReturnStatement"},
                    },
                )
            ],
            "One update executes the handler once and preserves the intended normalized description.",
            "Saving an Account completes once without a maximum trigger depth error.",
            "SELECT Id, Description FROM Account WHERE Id = :accountId",
            "Description is Normalized and one audit event was emitted.",
        )
    )

    cases.append(
        class_case(
            5,
            "Null identifier queried by controller",
            "data_integrity",
            "An Aura controller queries with a missing record identifier, returning a misleading query exception instead of a deterministic client error.",
            "FidelityNullGuardController",
            """public with sharing class FidelityNullGuardController {
    @AuraEnabled
    public static Account loadAccount(Id accountId) {
        return [SELECT Id, Name FROM Account WHERE Id = :accountId LIMIT 1];
    }
}""",
            [
                ("FidelityNullGuardController.loadAccount", "ApexMethod"),
                ("Account", "Object"),
                ("Account.Name", "CustomField"),
            ],
            [
                ("FidelityNullGuardController.loadAccount", "Account", "QUERIES", "FROM Account"),
                ("Account", "Account.Name", "READS_FIELD", "SELECT Id, Name"),
            ],
            [
                ast_instruction(
                    "insert_before",
                    "FidelityNullGuardController.loadAccount",
                    "SoqlQuery",
                    "query:Account",
                    {
                        "type": "IfStatement",
                        "condition": {
                            "type": "BinaryExpression",
                            "operator": "==",
                            "left": {"type": "Identifier", "name": "accountId"},
                            "right": {"type": "NullLiteral"},
                        },
                        "then": {
                            "type": "ThrowStatement",
                            "exception": "AuraHandledException",
                            "arguments": [{"type": "StringLiteral", "value": "Account id is required."}],
                        },
                    },
                )
            ],
            "A null identifier throws AuraHandledException before Limits.getQueries changes.",
            "Opening the component without record context shows Account id is required and no generic error.",
            "SELECT Id, Name FROM Account WHERE Id = :accountId",
            "A valid identifier still returns exactly one Account.",
        )
    )

    cases.append(
        class_case(
            6,
            "Missing field-level security enforcement",
            "security",
            "A cacheable controller returns annual revenue without checking field readability for the current user.",
            "FidelityRevenueController",
            """public with sharing class FidelityRevenueController {
    @AuraEnabled(cacheable=true)
    public static List<Account> loadRevenue(Set<Id> accountIds) {
        return [SELECT Id, Name, AnnualRevenue FROM Account WHERE Id IN :accountIds];
    }
}""",
            [
                ("FidelityRevenueController.loadRevenue", "ApexMethod"),
                ("Account.AnnualRevenue", "CustomField"),
                ("Standard User", "Profile"),
            ],
            [
                ("FidelityRevenueController.loadRevenue", "Account.AnnualRevenue", "READS_FIELD", "AnnualRevenue"),
                ("Account.AnnualRevenue", "Standard User", "GOVERNED_BY_FLS", "public static List<Account> loadRevenue"),
            ],
            [
                ast_instruction(
                    "replace_node",
                    "FidelityRevenueController.loadRevenue",
                    "SoqlQuery",
                    "query:Account",
                    {
                        "type": "SoqlQuery",
                        "sobject": "Account",
                        "fields": ["Id", "Name", "AnnualRevenue"],
                        "predicate": {"field": "Id", "operator": "IN", "binding": "accountIds"},
                        "access_level": "USER_MODE",
                        "security_enforced": True,
                    },
                )
            ],
            "A user without AnnualRevenue read access cannot retrieve the field; authorized users still can.",
            "The revenue column is absent for the Standard User and visible for the finance persona.",
            "SELECT Id, Name, AnnualRevenue FROM Account WITH USER_MODE",
            "The query respects the executing user's field permissions.",
        )
    )

    profile_path = source_path(7, "Guest Checkout.profile-meta.xml")
    write_text(
        profile_path,
        """<?xml version="1.0" encoding="UTF-8"?>
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <custom>true</custom>
    <fieldPermissions>
        <editable>false</editable>
        <field>Contact.SSN__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <objectPermissions>
        <allowCreate>false</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>false</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Contact</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
</Profile>""",
    )
    case7 = {
        "schema_version": "1.0.0",
        "id": "SF-FID-007",
        "title": "Guest profile exposes sensitive contact field",
        "category": "security",
        "showcase": "internal",
        "description": "A guest profile grants read access to an SSN field that is rendered by a public Experience Cloud component.",
        "source": {
            "fixtures": [{"path": profile_path, "sha256": sha256_file(ROOT / profile_path), "kind": "profile_metadata"}],
            "deployability": "requires_fixture_metadata",
            "prerequisites": ["Contact.SSN__c encrypted text fixture", "Experience Cloud guest user"],
            "entry_symbol": "Guest Checkout",
            "minimum_lines": 10,
        },
        "blast_radius": {
            "root": graph_node("Guest Checkout", "Profile"),
            "expected_nodes": [
                graph_node("Guest Checkout", "Profile"),
                graph_node("Contact.SSN__c", "CustomField"),
                graph_node("publicContactCard", "LWC"),
            ],
            "expected_edges": [
                {"from": "Guest Checkout", "to": "Contact.SSN__c", "kind": "GRANTS_READ", "evidence": {"fixture": profile_path, "needle": "<readable>true</readable>"}},
                {"from": "Contact.SSN__c", "to": "publicContactCard", "kind": "RENDERED_BY", "evidence": {"fixture": profile_path, "needle": "Contact.SSN__c"}},
            ],
            "required_hops": 2,
        },
        "patch_contract": {
            "output_format": "jataka.ast.instructions.v1",
            "raw_text_forbidden": True,
            "instructions": [metadata_update("Guest Checkout", "fieldPermissions:Contact.SSN__c", "Profile", "Guest Checkout", "fieldPermissions[Contact.SSN__c].readable", False)],
        },
        "verification": generic_verification(
            "Guest profile exposes sensitive contact field",
            "System.runAs guest-equivalent user cannot read Contact.SSN__c.",
            "The public contact card never renders an SSN value or field label.",
            "SELECT Id, SSN__c FROM Contact WITH USER_MODE",
            "Guest execution is denied field access while an authorized compliance user succeeds.",
        ),
        "expected_cleanup": {"scratch_org_destroyed": True, "browser_context_closed": True, "active_sandbox_destroyed": True, "no_zombie_after_reaper": True},
    }
    cases.append(case7)

    flow_path = source_path(8, "FidelityDiscountApproval.flow-meta.xml")
    write_text(
        flow_path,
        """<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>60.0</apiVersion>
    <label>Fidelity Discount Approval</label>
    <processType>AutoLaunchedFlow</processType>
    <recordUpdates>
        <name>Approve_Discount</name>
        <label>Approve Discount</label>
        <inputAssignments>
            <field>Discount_Approved__c</field>
            <value><booleanValue>true</booleanValue></value>
        </inputAssignments>
        <inputReference>$Record</inputReference>
    </recordUpdates>
    <start>
        <connector><targetReference>Approve_Discount</targetReference></connector>
        <object>Opportunity</object>
        <recordTriggerType>Update</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Active</status>
</Flow>""",
    )
    case8 = {
        "schema_version": "1.0.0",
        "id": "SF-FID-008",
        "title": "Flow update conflicts with validation rule",
        "category": "automation",
        "showcase": "internal",
        "description": "An after-save approval Flow updates a protected field without satisfying the opportunity validation rule's approval context.",
        "source": {
            "fixtures": [{"path": flow_path, "sha256": sha256_file(ROOT / flow_path), "kind": "flow_metadata"}],
            "deployability": "requires_fixture_metadata",
            "prerequisites": ["Opportunity.Discount_Approved__c", "Opportunity.Require_Approval_Context validation rule"],
            "entry_symbol": "FidelityDiscountApproval",
            "minimum_lines": 15,
        },
        "blast_radius": {
            "root": graph_node("Opportunity.Discount_Approved__c", "CustomField"),
            "expected_nodes": [
                graph_node("Opportunity.Discount_Approved__c", "CustomField"),
                graph_node("FidelityDiscountApproval", "Flow"),
                graph_node("Opportunity.Require_Approval_Context", "ValidationRule"),
            ],
            "expected_edges": [
                {"from": "Opportunity.Discount_Approved__c", "to": "FidelityDiscountApproval", "kind": "WRITTEN_BY", "evidence": {"fixture": flow_path, "needle": "<field>Discount_Approved__c</field>"}},
                {"from": "FidelityDiscountApproval", "to": "Opportunity.Require_Approval_Context", "kind": "TRIGGERS_VALIDATION", "evidence": {"fixture": flow_path, "needle": "<recordTriggerType>Update</recordTriggerType>"}},
            ],
            "required_hops": 2,
        },
        "patch_contract": {
            "output_format": "jataka.ast.instructions.v1",
            "raw_text_forbidden": True,
            "instructions": [metadata_update("FidelityDiscountApproval", "recordUpdate:Approve_Discount", "Flow", "FidelityDiscountApproval", "recordUpdates[Approve_Discount].inputAssignments[Approval_Context__c]", "AutomatedFlow")],
        },
        "verification": generic_verification(
            "Flow update conflicts with validation rule",
            "Updating an eligible Opportunity completes the Flow and leaves approval fields consistent.",
            "Approve Discount completes without a flow interview error.",
            "SELECT Id, Discount_Approved__c, Approval_Context__c FROM Opportunity WHERE Id = :opportunityId",
            "Discount is approved and context equals AutomatedFlow.",
        ),
        "expected_cleanup": {"scratch_org_destroyed": True, "browser_context_closed": True, "active_sandbox_destroyed": True, "no_zombie_after_reaper": True},
    }
    cases.append(case8)

    cases.append(
        class_case(
            9,
            "Mixed DML between user and account",
            "data_integrity",
            "One synchronous transaction updates a User and an Account, producing MIXED_DML_OPERATION in production onboarding.",
            "FidelityMixedDmlService",
            """public with sharing class FidelityMixedDmlService {
    public static void activateOwner(User owner, Account accountRecord) {
        owner.IsActive = true;
        update owner;
        accountRecord.OwnerId = owner.Id;
        update accountRecord;
    }
}""",
            [
                ("FidelityMixedDmlService.activateOwner", "ApexMethod"),
                ("User", "User"),
                ("Account", "Object"),
                ("FidelityOwnerAssignmentJob", "AsyncJob"),
            ],
            [
                ("FidelityMixedDmlService.activateOwner", "User", "UPDATES_SETUP_OBJECT", "update owner"),
                ("User", "Account", "MIXED_DML_WITH", "update accountRecord"),
                ("Account", "FidelityOwnerAssignmentJob", "DEFERRED_TO", "accountRecord.OwnerId"),
            ],
            [
                ast_instruction(
                    "replace_node",
                    "FidelityMixedDmlService.activateOwner",
                    "DmlStatement",
                    "update:Account",
                    {
                        "type": "AsyncEnqueue",
                        "job_type": "Queueable",
                        "job_symbol": "FidelityOwnerAssignmentJob",
                        "arguments": [{"type": "Identifier", "name": "accountRecord"}],
                    },
                )
            ],
            "The User update commits and the queueable assigns Account ownership in a separate transaction.",
            "Onboarding reaches Active without a mixed-DML error banner.",
            "SELECT Id, OwnerId FROM Account WHERE Id = :accountId",
            "OwnerId equals the activated user's Id after the queued job completes.",
            required_hops=3,
        )
    )

    cases.append(
        class_case(
            10,
            "Callout attempted after database update",
            "async",
            "An invoice method updates Opportunity before making an HTTP callout, causing uncommitted-work failure.",
            "FidelityInvoiceCalloutService",
            """public with sharing class FidelityInvoiceCalloutService {
    public static HttpResponse sendInvoice(Opportunity opportunityRecord) {
        opportunityRecord.Description = 'Invoice queued';
        update opportunityRecord;
        HttpRequest request = new HttpRequest();
        request.setEndpoint('callout:InvoiceGateway/invoices');
        request.setMethod('POST');
        return new Http().send(request);
    }
}""",
            [
                ("FidelityInvoiceCalloutService.sendInvoice", "ApexMethod"),
                ("Opportunity", "Object"),
                ("InvoiceGateway", "ManagedPackageBoundary"),
            ],
            [
                ("FidelityInvoiceCalloutService.sendInvoice", "Opportunity", "UPDATES", "update opportunityRecord"),
                ("Opportunity", "InvoiceGateway", "CALLOUT_AFTER_DML", "callout:InvoiceGateway/invoices"),
            ],
            [
                ast_instruction(
                    "replace_node",
                    "FidelityInvoiceCalloutService.sendInvoice",
                    "MethodBody",
                    "entire_body",
                    {
                        "type": "TransactionSequence",
                        "steps": [
                            method_call("InvoiceGatewayClient", "send", [{"type": "Identifier", "name": "opportunityRecord.Id"}]),
                            {"type": "DmlStatement", "operation": "UPDATE", "operand": "opportunityRecord"},
                        ],
                    },
                )
            ],
            "The callout executes before DML and the mocked 202 response is retained.",
            "Send Invoice completes and status changes to Invoice queued.",
            "SELECT Id, Description FROM Opportunity WHERE Id = :opportunityId",
            "Description changes only after the gateway returns success.",
        )
    )

    cases.append(
        class_case(
            11,
            "Unbounded activity query exhausts heap",
            "governor_limits",
            "A timeline controller loads every Task field and body for an Account without a selective cap or pagination.",
            "FidelityActivityTimelineController",
            """public with sharing class FidelityActivityTimelineController {
    @AuraEnabled(cacheable=true)
    public static List<Task> loadTimeline(Id accountId) {
        return [
            SELECT Id, Subject, Description, ActivityDate, WhoId, WhatId, CreatedDate
            FROM Task WHERE WhatId = :accountId ORDER BY CreatedDate DESC
        ];
    }
}""",
            [
                ("FidelityActivityTimelineController.loadTimeline", "ApexMethod"),
                ("Task", "Object"),
                ("Account", "Object"),
            ],
            [
                ("FidelityActivityTimelineController.loadTimeline", "Task", "QUERIES_UNBOUNDED", "FROM Task WHERE WhatId"),
                ("Task", "Account", "RELATES_TO", "WhatId = :accountId"),
            ],
            [
                ast_instruction(
                    "replace_node",
                    "FidelityActivityTimelineController.loadTimeline",
                    "SoqlQuery",
                    "query:Task",
                    {
                        "type": "SoqlQuery",
                        "sobject": "Task",
                        "fields": ["Id", "Subject", "ActivityDate", "WhoId", "WhatId", "CreatedDate"],
                        "predicate": {"field": "WhatId", "operator": "=", "binding": "accountId"},
                        "order_by": [{"field": "CreatedDate", "direction": "DESC"}],
                        "limit": 200,
                        "access_level": "USER_MODE",
                    },
                )
            ],
            "Ten thousand Tasks return at most 200 lightweight rows without heap failure.",
            "Timeline renders the latest 200 activities and offers deterministic pagination.",
            "SELECT COUNT() FROM Task WHERE WhatId = :accountId",
            "The total may exceed 200 while the controller result never does.",
        )
    )

    cases.append(
        class_case(
            12,
            "Dynamic SOQL filter injection",
            "security",
            "A search controller concatenates untrusted text into dynamic SOQL, allowing predicate injection and data overexposure.",
            "FidelityAccountSearchController",
            """public with sharing class FidelityAccountSearchController {
    @AuraEnabled(cacheable=true)
    public static List<Account> search(String searchTerm) {
        String queryValue = 'SELECT Id, Name FROM Account WHERE Name LIKE \\'%' +
            searchTerm + '%\\' LIMIT 50';
        return Database.query(queryValue);
    }
}""",
            [
                ("FidelityAccountSearchController.search", "ApexMethod"),
                ("Database.query", "ApexMethod"),
                ("Account.Name", "CustomField"),
            ],
            [
                ("FidelityAccountSearchController.search", "Database.query", "CALLS_DYNAMIC", "Database.query(queryValue)"),
                ("Database.query", "Account.Name", "CONCATENATES_INPUT", "searchTerm + '%"),
            ],
            [
                ast_instruction(
                    "replace_node",
                    "FidelityAccountSearchController.search",
                    "MethodBody",
                    "dynamic_query",
                    {
                        "type": "BoundSoqlExecution",
                        "query": {
                            "type": "SoqlQuery",
                            "sobject": "Account",
                            "fields": ["Id", "Name"],
                            "predicate": {"field": "Name", "operator": "LIKE", "binding": "normalizedSearchTerm"},
                            "limit": 50,
                            "access_level": "USER_MODE",
                        },
                        "bindings": {
                            "normalizedSearchTerm": {
                                "type": "StringConcat",
                                "parts": ["%", {"type": "Identifier", "name": "searchTerm"}, "%"],
                            }
                        },
                    },
                )
            ],
            "Injection payloads are treated as literal search text and return no unauthorized rows.",
            "Entering a quote-based payload does not broaden results or expose a generic error.",
            "SELECT Id, Name FROM Account WHERE Name LIKE :normalizedSearchTerm WITH USER_MODE LIMIT 50",
            "Only names containing the literal normalized term are returned.",
        )
    )

    cases.append(
        class_case(
            13,
            "Stale account overwrite loses concurrent edit",
            "data_integrity",
            "A service updates a detached Account snapshot without checking SystemModstamp, silently overwriting a concurrent user's change.",
            "FidelityOptimisticLockService",
            """public with sharing class FidelityOptimisticLockService {
    public static void renameAccount(Account detachedRecord) {
        update detachedRecord;
    }
}""",
            [
                ("FidelityOptimisticLockService.renameAccount", "ApexMethod"),
                ("Account", "Object"),
                ("Account.SystemModstamp", "CustomField"),
            ],
            [
                ("FidelityOptimisticLockService.renameAccount", "Account", "UPDATES_STALE", "update detachedRecord"),
                ("Account", "Account.SystemModstamp", "REQUIRES_VERSION", "detachedRecord"),
            ],
            [
                ast_instruction(
                    "insert_before",
                    "FidelityOptimisticLockService.renameAccount",
                    "DmlStatement",
                    "update:detachedRecord",
                    {
                        "type": "OptimisticLockCheck",
                        "sobject": "Account",
                        "id_expression": {"type": "FieldAccess", "receiver": "detachedRecord", "field": "Id"},
                        "version_field": "SystemModstamp",
                        "on_conflict": {"type": "ThrowStatement", "exception": "AuraHandledException", "arguments": [{"type": "StringLiteral", "value": "Account changed; refresh before saving."}]},
                    },
                )
            ],
            "A concurrent edit causes a deterministic conflict and preserves the newer database value.",
            "A stale editor sees a refresh-required message instead of a false success.",
            "SELECT Id, Name, SystemModstamp FROM Account WHERE Id = :accountId",
            "Name remains the value from the most recent committed editor.",
        )
    )

    cases.append(
        class_case(
            14,
            "Without-sharing case export leaks records",
            "security",
            "An export controller runs without sharing and returns Cases outside the caller's row-level access.",
            "FidelityCaseExportController",
            """public without sharing class FidelityCaseExportController {
    @AuraEnabled
    public static List<Case> exportOpenCases() {
        return [SELECT Id, CaseNumber, Subject, ContactEmail FROM Case WHERE IsClosed = false];
    }
}""",
            [
                ("FidelityCaseExportController", "ApexClass"),
                ("FidelityCaseExportController.exportOpenCases", "ApexMethod"),
                ("Case", "Object"),
            ],
            [
                ("FidelityCaseExportController", "FidelityCaseExportController.exportOpenCases", "DECLARES", "exportOpenCases"),
                ("FidelityCaseExportController.exportOpenCases", "Case", "QUERIES_WITHOUT_SHARING", "FROM Case WHERE IsClosed"),
            ],
            [
                ast_instruction(
                    "replace_node",
                    "FidelityCaseExportController",
                    "SharingDeclaration",
                    "without sharing",
                    {"type": "SharingDeclaration", "mode": "WITH_SHARING"},
                ),
                ast_instruction(
                    "replace_node",
                    "FidelityCaseExportController.exportOpenCases",
                    "SoqlQuery",
                    "query:Case",
                    {
                        "type": "SoqlQuery",
                        "sobject": "Case",
                        "fields": ["Id", "CaseNumber", "Subject", "ContactEmail"],
                        "predicate": {"field": "IsClosed", "operator": "=", "value": False},
                        "access_level": "USER_MODE",
                    },
                ),
            ],
            "Restricted users receive only shared Cases and field-level access is enforced.",
            "Export contains only Cases visible in the user's standard list view.",
            "SELECT Id, CaseNumber, Subject, ContactEmail FROM Case WHERE IsClosed = false WITH USER_MODE",
            "The result Id set equals the user's accessible Case Id set.",
        )
    )

    # Five-hop external showcase.
    case15_id = "SF-FID-015"
    field_path = source_path(15, "objects/Account/fields/Jataka_Credit_Score__c.field-meta.xml")
    flow15_path = source_path(15, "flows/FidelityCreditReview.flow-meta.xml")
    class15_path = source_path(15, "classes/FidelityCreditAction.cls")
    class15_meta = source_path(15, "classes/FidelityCreditAction.cls-meta.xml")
    boundary_path = source_path(15, "managed-boundary.json")
    rule_path = source_path(15, "objects/Account/validationRules/Fidelity_Credit_Gate.validationRule-meta.xml")
    write_text(field_path, """<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Jataka_Credit_Score__c</fullName>
    <externalId>false</externalId>
    <label>Jataka Credit Score</label>
    <precision>3</precision>
    <required>false</required>
    <scale>0</scale>
    <type>Number</type>
    <unique>false</unique>
</CustomField>""")
    write_text(flow15_path, """<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>60.0</apiVersion>
    <actionCalls>
        <name>Invoke_Credit_Action</name>
        <actionName>FidelityCreditAction.evaluate</actionName>
        <actionType>apex</actionType>
        <inputParameters>
            <name>accountId</name>
            <value><elementReference>$Record.Id</elementReference></value>
        </inputParameters>
    </actionCalls>
    <label>Fidelity Credit Review</label>
    <processType>AutoLaunchedFlow</processType>
    <start>
        <connector><targetReference>Invoke_Credit_Action</targetReference></connector>
        <filters>
            <field>Jataka_Credit_Score__c</field>
            <operator>IsChanged</operator>
            <value><booleanValue>true</booleanValue></value>
        </filters>
        <object>Account</object>
        <recordTriggerType>Update</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>
    <status>Active</status>
</Flow>""")
    write_text(class15_path, """public with sharing class FidelityCreditAction {
    public class Input {
        @InvocableVariable(required=true) public Id accountId;
    }
    @InvocableMethod(label='Evaluate Credit')
    public static void evaluate(List<Input> inputs) {
        Type managedType = Type.forName('ncino', 'CreditDecisionService');
        for (Input item : inputs) {
            Account accountRecord = [
                SELECT Id, Jataka_Credit_Score__c, Rating FROM Account WHERE Id = :item.accountId
            ];
            if (managedType != null && accountRecord.Jataka_Credit_Score__c != null) {
                Object managedService = managedType.newInstance();
                accountRecord.Rating = managedService == null ? 'Warm' : 'Hot';
                update accountRecord;
            }
        }
    }
}""")
    write_text(class15_meta, apex_meta())
    write_json(boundary_path, {
        "namespace": "ncino",
        "symbol": "CreditDecisionService",
        "entry_method": "evaluate",
        "transaction_effect": "Account.Rating becomes Hot",
        "downstream_validation_rule": "Account.Fidelity_Credit_Gate",
    })
    write_text(rule_path, """<?xml version="1.0" encoding="UTF-8"?>
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <errorConditionFormula>AND(Rating = "Hot", Jataka_Credit_Score__c &lt; 600)</errorConditionFormula>
    <errorMessage>Hot credit decisions require a score of at least 600.</errorMessage>
</ValidationRule>""")
    fixture15 = [
        (field_path, "object_metadata"),
        (flow15_path, "flow_metadata"),
        (class15_path, "apex_class"),
        (class15_meta, "apex_metadata"),
        (boundary_path, "boundary_contract"),
        (rule_path, "validation_rule_metadata"),
    ]
    cases.append({
        "schema_version": "1.0.0",
        "id": case15_id,
        "title": "Five-hop managed-package dependency chain",
        "category": "dependency_graph",
        "showcase": "hidden_dependency_5_hop",
        "description": "A custom field starts a Flow, invokes Apex, crosses a managed-package namespace, and reaches a validation rule through the same transaction.",
        "source": {
            "fixtures": [{"path": path, "sha256": sha256_file(ROOT / path), "kind": kind} for path, kind in fixture15],
            "deployability": "requires_managed_package_stub",
            "prerequisites": ["A benchmark stub or licensed ncino.CreditDecisionService implementation"],
            "entry_symbol": "Account.Jataka_Credit_Score__c",
            "minimum_lines": 50,
        },
        "blast_radius": {
            "root": graph_node("Account.Jataka_Credit_Score__c", "CustomField"),
            "expected_nodes": [
                graph_node("Account.Jataka_Credit_Score__c", "CustomField"),
                graph_node("FidelityCreditReview", "Flow"),
                graph_node("FidelityCreditAction", "ApexClass"),
                graph_node("FidelityCreditAction.evaluate", "ApexMethod"),
                graph_node("ncino.CreditDecisionService", "ManagedPackageBoundary"),
                graph_node("Account.Fidelity_Credit_Gate", "ValidationRule"),
            ],
            "expected_edges": [
                {"from": "Account.Jataka_Credit_Score__c", "to": "FidelityCreditReview", "kind": "STARTS_FLOW", "evidence": {"fixture": flow15_path, "needle": "<field>Jataka_Credit_Score__c</field>"}},
                {"from": "FidelityCreditReview", "to": "FidelityCreditAction", "kind": "INVOKES_APEX", "evidence": {"fixture": flow15_path, "needle": "<actionName>FidelityCreditAction.evaluate</actionName>"}},
                {"from": "FidelityCreditAction", "to": "FidelityCreditAction.evaluate", "kind": "DECLARES", "evidence": {"fixture": class15_path, "needle": "public static void evaluate"}},
                {"from": "FidelityCreditAction.evaluate", "to": "ncino.CreditDecisionService", "kind": "RESOLVES_NAMESPACE", "evidence": {"fixture": class15_path, "needle": "Type.forName('ncino', 'CreditDecisionService')"}},
                {"from": "ncino.CreditDecisionService", "to": "Account.Fidelity_Credit_Gate", "kind": "TRIGGERS_VALIDATION", "evidence": {"fixture": boundary_path, "needle": "Account.Fidelity_Credit_Gate"}},
            ],
            "required_hops": 5,
        },
        "patch_contract": {
            "output_format": "jataka.ast.instructions.v1",
            "raw_text_forbidden": True,
            "instructions": [
                ast_instruction(
                    "insert_before",
                    "FidelityCreditAction.evaluate",
                    "DmlStatement",
                    "update:accountRecord",
                    {
                        "type": "IfStatement",
                        "condition": {"type": "BinaryExpression", "operator": "<", "left": {"type": "FieldAccess", "receiver": "accountRecord", "field": "Jataka_Credit_Score__c"}, "right": {"type": "IntegerLiteral", "value": 600}},
                        "then": {"type": "Assignment", "target": {"type": "FieldAccess", "receiver": "accountRecord", "field": "Rating"}, "value": {"type": "StringLiteral", "value": "Warm"}},
                    },
                )
            ],
        },
        "verification": generic_verification(
            "Five-hop managed-package dependency chain",
            "Scores below 600 remain Warm and the complete five-hop dependency path is attached to the test result.",
            "Credit review saves successfully and displays the package decision with its validation rationale.",
            "SELECT Id, Jataka_Credit_Score__c, Rating FROM Account WHERE Id = :accountId",
            "A score below 600 never persists Rating=Hot.",
        ),
        "expected_cleanup": {"scratch_org_destroyed": True, "browser_context_closed": True, "active_sandbox_destroyed": True, "no_zombie_after_reaper": True},
    })

    large = large_class()
    cases.append(
        class_case(
            16,
            "One-thousand-line deterministic bulkification",
            "compiler",
            "A 1,000-plus-line Apex service contains one unsafe query loop; the benchmark requires a localized AST transformation without regenerating the class.",
            "FidelityLargeInvoiceService",
            large,
            [
                ("FidelityLargeInvoiceService.calculateTotals", "ApexMethod"),
                ("Account", "Object"),
                ("Opportunity.AccountId", "CustomField"),
            ],
            [
                ("FidelityLargeInvoiceService.calculateTotals", "Account", "ITERATES", "for (Account accountRecord : accounts)"),
                ("Account", "Opportunity.AccountId", "QUERIES_BY", "WHERE AccountId = :accountRecord.Id"),
            ],
            [
                ast_instruction(
                    "replace_node",
                    "FidelityLargeInvoiceService.calculateTotals",
                    "ForStatement",
                    "loop:accountRecord",
                    {
                        "type": "BulkAggregatePlan",
                        "query": {
                            "type": "SoqlAggregateQuery",
                            "sobject": "Opportunity",
                            "group_by": "AccountId",
                            "aggregates": [{"function": "SUM", "field": "Amount", "alias": "total"}],
                            "predicate": {"field": "AccountId", "operator": "IN", "binding": "accountIds"},
                        },
                        "result_map": {"key": "AccountId", "value": "total", "default": 0},
                    },
                )
            ],
            "The deterministic output retains every helper and compiles on attempt one while totals remain exact.",
            "The invoice totals panel renders accurate totals for 200 Accounts.",
            "SELECT AccountId, SUM(Amount) total FROM Opportunity WHERE AccountId IN :accountIds GROUP BY AccountId",
            "Aggregate values equal calculateTotals for every Account.",
            showcase="zero_syntax_1000_line",
            minimum_lines=1000,
        )
    )

    audit_path = source_path(17, "salesforce-setup-audit-event.json")
    github_path = source_path(17, "github-profile-state.json")
    write_json(audit_path, {
        "event_id": "0YmFidelity000017",
        "event_type": "ProfilePermissionChanged",
        "actor": "rogue.admin@example.test",
        "member": "Finance Analyst",
        "permission": "Financial_Dashboard__c.read",
        "old_value": True,
        "new_value": False,
        "valid_time": "2026-07-23T08:15:00Z",
        "observed_time": "2026-07-23T08:15:07Z",
    })
    write_json(github_path, {
        "commit": "f17e17f17e17f17e17f17e17f17e17f17e17f17e",
        "member": "Finance Analyst",
        "permission": "Financial_Dashboard__c.read",
        "value": True,
        "transaction_time": "2026-07-23T07:55:00Z",
    })
    cases.append({
        "schema_version": "1.0.0",
        "id": "SF-FID-017",
        "title": "Bitemporal orphaned profile permission",
        "category": "bitemporal",
        "showcase": "bitemporal_orphan_drift",
        "description": "A production admin removes dashboard access outside GitHub, creating a valid-time state that disagrees with transaction-time source control.",
        "source": {
            "fixtures": [
                {"path": audit_path, "sha256": sha256_file(ROOT / audit_path), "kind": "audit_event"},
                {"path": github_path, "sha256": sha256_file(ROOT / github_path), "kind": "github_state"},
            ],
            "deployability": "event_replay_only",
            "prerequisites": ["Kafka audit topic", "Temporal Salesforce audit workflow", "Neo4j bitemporal projection"],
            "entry_symbol": "Finance Analyst.Financial_Dashboard__c.read",
            "minimum_lines": 10,
        },
        "blast_radius": {
            "root": graph_node("0YmFidelity000017", "AuditEvent"),
            "expected_nodes": [
                graph_node("0YmFidelity000017", "AuditEvent"),
                graph_node("Finance Analyst", "Profile"),
                graph_node("finance.user@example.test", "User"),
                graph_node("financialDashboard", "LWC"),
            ],
            "expected_edges": [
                {"from": "0YmFidelity000017", "to": "Finance Analyst", "kind": "CHANGES_VALID_TIME", "evidence": {"fixture": audit_path, "needle": "ProfilePermissionChanged"}},
                {"from": "Finance Analyst", "to": "finance.user@example.test", "kind": "ASSIGNED_TO", "evidence": {"fixture": audit_path, "needle": "Finance Analyst"}},
                {"from": "finance.user@example.test", "to": "financialDashboard", "kind": "LOSES_ACCESS_TO", "evidence": {"fixture": github_path, "needle": "Financial_Dashboard__c.read"}},
            ],
            "required_hops": 3,
        },
        "patch_contract": {
            "output_format": "jataka.ast.instructions.v1",
            "raw_text_forbidden": True,
            "instructions": [metadata_update("Finance Analyst", "objectPermissions:Financial_Dashboard__c", "Profile", "Finance Analyst", "objectPermissions[Financial_Dashboard__c].allowRead", True)],
        },
        "verification": generic_verification(
            "Bitemporal orphaned profile permission",
            "Event replay creates one drift incident with distinct valid_time and transaction_time.",
            "The affected user regains the Financial Dashboard only after approval and sees the drift attribution.",
            "MATCH (p:Profile {name:'Finance Analyst'}) RETURN p.valid_time, p.transaction_time, p.drift_status",
            "drift_status moves from ORPHANED to RECONCILED and both timestamps remain auditable.",
        ),
        "expected_cleanup": {"scratch_org_destroyed": True, "browser_context_closed": True, "active_sandbox_destroyed": True, "no_zombie_after_reaper": True},
    })

    cases.append(
        class_case(
            18,
            "All-or-none bulk integration rollback",
            "data_integrity",
            "A bulk integration uses all-or-none DML, so one malformed Account rolls back hundreds of valid records without record-level evidence.",
            "FidelityPartialSaveService",
            """public with sharing class FidelityPartialSaveService {
    public static void saveAccounts(List<Account> accounts) {
        insert accounts;
    }
}""",
            [
                ("FidelityPartialSaveService.saveAccounts", "ApexMethod"),
                ("Account", "Object"),
                ("AccountValidationRules", "ValidationRule"),
            ],
            [
                ("FidelityPartialSaveService.saveAccounts", "Account", "INSERTS_ALL_OR_NONE", "insert accounts"),
                ("Account", "AccountValidationRules", "EVALUATED_BY", "List<Account> accounts"),
            ],
            [
                ast_instruction(
                    "replace_node",
                    "FidelityPartialSaveService.saveAccounts",
                    "DmlStatement",
                    "insert:accounts",
                    {
                        "type": "DatabaseDml",
                        "operation": "INSERT",
                        "records": {"type": "Identifier", "name": "accounts"},
                        "all_or_none": False,
                        "capture_results": True,
                    },
                )
            ],
            "Valid records commit, invalid rows return indexed errors, and no failure is silently dropped.",
            "Bulk import shows independent success and error counts with downloadable row details.",
            "SELECT Id, Name FROM Account WHERE Name LIKE 'Fidelity Partial %'",
            "The count equals valid input rows, not zero and not total input rows.",
        )
    )

    cases.append(
        class_case(
            19,
            "User-timezone renewal date drift",
            "data_integrity",
            "A renewal scheduler converts DateTime through the running user's timezone, shifting boundary-date renewals for global users.",
            "FidelityRenewalDateService",
            """public with sharing class FidelityRenewalDateService {
    public static Date renewalDate(Datetime contractEnd) {
        return contractEnd.date();
    }
}""",
            [
                ("FidelityRenewalDateService.renewalDate", "ApexMethod"),
                ("User.TimeZoneSidKey", "CustomField"),
                ("Contract.EndDate", "CustomField"),
            ],
            [
                ("FidelityRenewalDateService.renewalDate", "User.TimeZoneSidKey", "IMPLICIT_TIMEZONE", "contractEnd.date()"),
                ("User.TimeZoneSidKey", "Contract.EndDate", "SHIFTS_DATE", "return contractEnd.date()"),
            ],
            [
                ast_instruction(
                    "replace_node",
                    "FidelityRenewalDateService.renewalDate",
                    "MethodCall",
                    "contractEnd.date",
                    method_call("contractEnd", "dateGmt", []),
                )
            ],
            "Users in UTC-8 and UTC+10 receive the same contractual date for the same instant.",
            "The renewal date displayed in both personas matches the UTC contractual date.",
            "SELECT Id, EndDate FROM Contract WHERE Id = :contractId",
            "EndDate equals the dateGmt-derived expected date.",
        )
    )

    cases.append(
        class_case(
            20,
            "Duplicate platform event delivery",
            "async",
            "A platform-event consumer creates a Case on every delivery without an idempotency key, duplicating incidents after replay.",
            "FidelityEventConsumer",
            """public with sharing class FidelityEventConsumer {
    public static void consume(List<Map<String, Object>> events) {
        List<Case> casesToInsert = new List<Case>();
        for (Map<String, Object> eventRecord : events) {
            casesToInsert.add(new Case(
                Subject = String.valueOf(eventRecord.get('subject')),
                Origin = 'Web'
            ));
        }
        insert casesToInsert;
    }
}""",
            [
                ("FidelityIncidentEvent", "PlatformEvent"),
                ("FidelityEventConsumer.consume", "ApexMethod"),
                ("Case", "Object"),
            ],
            [
                ("FidelityIncidentEvent", "FidelityEventConsumer.consume", "DELIVERED_TO", "List<Map<String, Object>> events"),
                ("FidelityEventConsumer.consume", "Case", "CREATES_WITHOUT_KEY", "insert casesToInsert"),
            ],
            [
                ast_instruction(
                    "insert_before",
                    "FidelityEventConsumer.consume",
                    "CollectionAdd",
                    "casesToInsert.add",
                    {
                        "type": "IdempotencyFilter",
                        "key_expression": {
                            "type": "MapGet",
                            "map": "eventRecord",
                            "key": "eventUuid",
                        },
                        "lookup_field": "Case.External_Event_Id__c",
                        "on_duplicate": "SKIP",
                    },
                )
            ],
            "Publishing the same event UUID twice creates exactly one Case.",
            "The incident console shows one Case and an idempotent replay annotation.",
            "SELECT Id, External_Event_Id__c FROM Case WHERE External_Event_Id__c = :eventUuid",
            "Exactly one Case exists for the event UUID.",
        )
    )

    if len(cases) != 20:
        raise RuntimeError(f"Expected 20 cases, built {len(cases)}")
    return cases


def freeze(cases: list[dict[str, Any]]) -> None:
    for case in cases:
        write_json(f"cases/{case['id']}.json", case)

    case_entries = []
    for case in cases:
        relative = f"cases/{case['id']}.json"
        case_entries.append(
            {"id": case["id"], "path": relative, "sha256": sha256_file(ROOT / relative)}
        )
    manifest = {
        "schema_version": "1.0.0",
        "benchmark_id": "salesforce-fidelity-v1",
        "title": "Jataka Internal Salesforce Fidelity Benchmark",
        "case_count": 20,
        "release_gate": {
            "blast_radius_accuracy": 0.8,
            "first_pass_compilation": 0.8,
            "sandbox_verification": 0.8,
        },
        "required_showcases": [
            "hidden_dependency_5_hop",
            "zero_syntax_1000_line",
            "hidden_interprocedural_o_n2",
            "bitemporal_orphan_drift",
        ],
        "cases": case_entries,
    }
    write_json("manifest.json", manifest)

    governed = sorted(
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.name != "corpus.lock.json"
        and "__pycache__" not in path.parts
        and not path.name.endswith(".pyc")
    )
    file_hashes = {relative: sha256_file(ROOT / relative) for relative in governed}
    lock = {
        "schema_version": "1.0.0",
        "algorithm": "sha256",
        "corpus_sha256": hashlib.sha256(canonical_bytes(file_hashes)).hexdigest(),
        "files": file_hashes,
    }
    write_json("corpus.lock.json", lock)


def main() -> None:
    freeze(build_cases())
    print(f"Frozen 20 cases at {ROOT}")


if __name__ == "__main__":
    main()
