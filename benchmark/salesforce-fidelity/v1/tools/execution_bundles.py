#!/usr/bin/env python3
"""Build isolated Salesforce source-format projects for fidelity cases."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any


API_VERSION = "60.0"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True))


def apex_meta() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>{API_VERSION}</apiVersion>
    <status>Active</status>
</ApexClass>"""


def trigger_meta() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ApexTrigger xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>{API_VERSION}</apiVersion>
    <status>Active</status>
</ApexTrigger>"""


def custom_field(
    full_name: str,
    label: str,
    field_type: str,
    *,
    length: int | None = None,
    unique: bool = False,
    external_id: bool = False,
) -> str:
    details = ""
    if length is not None:
        details += f"\n    <length>{length}</length>"
    default = (
        "\n    <defaultValue>false</defaultValue>"
        if field_type == "Checkbox"
        else "\n    <required>false</required>"
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>{full_name}</fullName>
    <externalId>{str(external_id).lower()}</externalId>
    <label>{label}</label>{details}{default}
    <type>{field_type}</type>
    <unique>{str(unique).lower()}</unique>
</CustomField>"""


def test_class(case_id: str, body: str) -> tuple[str, str]:
    class_name = f"FidelityBenchmark{case_id[-3:]}Test"
    source = f"""@IsTest
private class {class_name} {{
{body.rstrip()}
}}"""
    return class_name, source


TEST_BODIES: dict[str, str] = {
    "SF-FID-001": """    @IsTest
    static void verifiesBulkContactCounting() {
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 101; i++) {
            accounts.add(new Account(Name = 'Fidelity Direct ' + i));
        }
        insert accounts;
        Test.startTest();
        Map<Id, Integer> counts = FidelityDirectQueryService.contactCounts(accounts);
        Test.stopTest();
        System.assertEquals(101, counts.size());
    }""",
    "SF-FID-002": """    @IsTest
    static void verifiesSingleDmlBulkClose() {
        Account accountRecord = new Account(Name = 'Fidelity DML');
        insert accountRecord;
        List<Opportunity> records = new List<Opportunity>();
        for (Integer i = 0; i < 151; i++) {
            records.add(new Opportunity(
                AccountId = accountRecord.Id,
                Name = 'Fidelity Opportunity ' + i,
                StageName = 'Prospecting',
                CloseDate = Date.today().addDays(30)
            ));
        }
        insert records;
        Test.startTest();
        FidelityDmlLoopService.closeWon(records);
        Test.stopTest();
        System.assertEquals('Closed Won', records[0].StageName);
    }""",
    "SF-FID-003": """    @IsTest
    static void verifiesIndexedScores() {
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 200; i++) {
            accounts.add(new Account(Name = 'Fidelity Quadratic ' + i));
        }
        insert accounts;
        List<Contact> contacts = new List<Contact>();
        for (Account accountRecord : accounts) {
            contacts.add(new Contact(
                AccountId = accountRecord.Id,
                LastName = accountRecord.Name
            ));
        }
        insert contacts;
        Test.startTest();
        Map<Id, Integer> scores =
            FidelityHiddenQuadraticService.scoreAccounts(accounts, contacts);
        Integer elapsed = Limits.getCpuTime();
        Test.stopTest();
        System.assertEquals(200, scores.size());
        System.assert(elapsed < 5000, 'Expected bounded CPU consumption');
    }""",
    "SF-FID-004": """    @IsTest
    static void verifiesTriggerDoesNotReenter() {
        Account accountRecord = new Account(Name = 'Fidelity Recursion');
        insert accountRecord;
        Test.startTest();
        accountRecord.Name = 'Fidelity Recursion Updated';
        update accountRecord;
        Test.stopTest();
        System.assertEquals(
            'Normalized',
            [SELECT Description FROM Account WHERE Id = :accountRecord.Id].Description
        );
    }""",
    "SF-FID-005": """    @IsTest
    static void verifiesNullGuardRunsBeforeQuery() {
        Integer beforeQueries = Limits.getQueries();
        try {
            FidelityNullGuardController.loadAccount(null);
            System.assert(false, 'Expected AuraHandledException');
        } catch (AuraHandledException expected) {
            System.assertEquals(beforeQueries, Limits.getQueries());
        }
    }""",
    "SF-FID-006": """    @IsTest
    static void verifiesAuthorizedRevenueQueryStillWorks() {
        Account accountRecord =
            new Account(Name = 'Fidelity Revenue', AnnualRevenue = 250000);
        insert accountRecord;
        Test.startTest();
        List<Account> result =
            FidelityRevenueController.loadRevenue(new Set<Id>{accountRecord.Id});
        Test.stopTest();
        System.assertEquals(1, result.size());
        System.assertEquals(250000, result[0].AnnualRevenue);
    }""",
    "SF-FID-007": """    @IsTest
    static void verifiesSensitiveFieldReadIsRemoved() {
        List<FieldPermissions> permissions = [
            SELECT Field, PermissionsRead, Parent.Name
            FROM FieldPermissions
            WHERE Field = 'Contact.SSN__c' AND Parent.Name = 'Guest Checkout'
        ];
        System.assertEquals(1, permissions.size());
        System.assertEquals(false, permissions[0].PermissionsRead);
    }""",
    "SF-FID-008": """    @IsTest
    static void verifiesFlowSuppliesApprovalContext() {
        Account accountRecord = new Account(Name = 'Fidelity Flow');
        insert accountRecord;
        Opportunity opportunityRecord = new Opportunity(
            AccountId = accountRecord.Id,
            Name = 'Fidelity Discount',
            StageName = 'Prospecting',
            CloseDate = Date.today().addDays(30)
        );
        insert opportunityRecord;
        Test.startTest();
        opportunityRecord.Description = 'Trigger approval';
        update opportunityRecord;
        Test.stopTest();
        Opportunity actual = [
            SELECT Discount_Approved__c, Approval_Context__c
            FROM Opportunity WHERE Id = :opportunityRecord.Id
        ];
        System.assertEquals(true, actual.Discount_Approved__c);
        System.assertEquals('AutomatedFlow', actual.Approval_Context__c);
    }""",
    "SF-FID-009": """    @IsTest
    static void verifiesSetupDmlIsSeparated() {
        Account accountRecord = new Account(Name = 'Fidelity Mixed DML');
        insert accountRecord;
        User owner = [SELECT Id, IsActive FROM User WHERE Id = :UserInfo.getUserId()];
        Test.startTest();
        FidelityMixedDmlService.activateOwner(owner, accountRecord);
        Test.stopTest();
        System.assertEquals(
            owner.Id,
            [SELECT OwnerId FROM Account WHERE Id = :accountRecord.Id].OwnerId
        );
    }""",
    "SF-FID-010": """    private class GatewayMock implements HttpCalloutMock {
        public HttpResponse respond(HttpRequest request) {
            HttpResponse response = new HttpResponse();
            response.setStatusCode(202);
            response.setBody('{"accepted":true}');
            return response;
        }
    }

    @TestSetup
    static void seed() {
        insert new Opportunity(
            Name = 'Fidelity Invoice',
            StageName = 'Prospecting',
            CloseDate = Date.today().addDays(30)
        );
    }

    @IsTest
    static void verifiesCalloutBeforeDml() {
        Opportunity opportunityRecord = [
            SELECT Id, Description FROM Opportunity LIMIT 1
        ];
        Test.setMock(HttpCalloutMock.class, new GatewayMock());
        Test.startTest();
        HttpResponse response =
            FidelityInvoiceCalloutService.sendInvoice(opportunityRecord);
        Test.stopTest();
        System.assertEquals(202, response.getStatusCode());
        System.assertEquals(
            'Invoice queued',
            [SELECT Description FROM Opportunity WHERE Id = :opportunityRecord.Id].Description
        );
    }""",
    "SF-FID-011": """    @TestSetup
    static void seed() {
        Account accountRecord = new Account(Name = 'Fidelity Timeline');
        insert accountRecord;
        List<Task> tasks = new List<Task>();
        for (Integer i = 0; i < 201; i++) {
            tasks.add(new Task(
                WhatId = accountRecord.Id,
                Subject = 'Fidelity Activity ' + i,
                Status = 'Not Started',
                Priority = 'Normal'
            ));
        }
        insert tasks;
    }

    @IsTest
    static void verifiesTimelineIsCapped() {
        Id accountId = [SELECT Id FROM Account LIMIT 1].Id;
        Test.startTest();
        List<Task> timeline =
            FidelityActivityTimelineController.loadTimeline(accountId);
        Test.stopTest();
        System.assertLessThanOrEqual(200, timeline.size());
    }""",
    "SF-FID-012": """    @TestSetup
    static void seed() {
        insert new List<Account>{
            new Account(Name = 'Fidelity Search Alpha'),
            new Account(Name = 'Fidelity Search Beta')
        };
    }

    @IsTest
    static void verifiesInputIsBound() {
        Test.startTest();
        List<Account> result =
            FidelityAccountSearchController.search('%\\' OR Name != \\'');
        Test.stopTest();
        System.assertEquals(0, result.size());
    }""",
    "SF-FID-013": """    @IsTest
    static void verifiesNormalRenameRemainsSupported() {
        Account accountRecord = new Account(Name = 'Fidelity Original');
        insert accountRecord;
        accountRecord.Name = 'Fidelity Renamed';
        Test.startTest();
        FidelityOptimisticLockService.renameAccount(accountRecord);
        Test.stopTest();
        System.assertEquals(
            'Fidelity Renamed',
            [SELECT Name FROM Account WHERE Id = :accountRecord.Id].Name
        );
    }""",
    "SF-FID-014": """    @IsTest
    static void verifiesExportUsesEnforcedAccessMode() {
        insert new Case(Subject = 'Fidelity Export', Origin = 'Web');
        Test.startTest();
        List<Case> result = FidelityCaseExportController.exportOpenCases();
        Test.stopTest();
        System.assertEquals(1, result.size());
    }""",
    "SF-FID-015": """    @IsTest
    static void verifiesLowScoreCannotBecomeHot() {
        Account accountRecord = new Account(
            Name = 'Fidelity Credit',
            Jataka_Credit_Score__c = 550,
            Rating = 'Warm'
        );
        insert accountRecord;
        FidelityCreditAction.Input input = new FidelityCreditAction.Input();
        input.accountId = accountRecord.Id;
        Test.startTest();
        FidelityCreditAction.evaluate(new List<FidelityCreditAction.Input>{input});
        Test.stopTest();
        System.assertEquals(
            'Warm',
            [SELECT Rating FROM Account WHERE Id = :accountRecord.Id].Rating
        );
    }""",
    "SF-FID-016": """    @IsTest
    static void verifiesAggregateTotals() {
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 101; i++) {
            accounts.add(new Account(Name = 'Fidelity Large ' + i));
        }
        insert accounts;
        List<Opportunity> opportunities = new List<Opportunity>();
        for (Account accountRecord : accounts) {
            opportunities.add(new Opportunity(
                AccountId = accountRecord.Id,
                Name = 'Fidelity Invoice ' + accountRecord.Name,
                Amount = 10,
                StageName = 'Prospecting',
                CloseDate = Date.today().addDays(30)
            ));
        }
        insert opportunities;
        Test.startTest();
        Map<Id, Decimal> totals =
            FidelityLargeInvoiceService.calculateTotals(accounts);
        Test.stopTest();
        System.assertEquals(10, totals.get(accounts[0].Id));
    }""",
    "SF-FID-018": """    @IsTest
    static void verifiesPartialSaveRetainsValidRows() {
        List<Account> records = new List<Account>{
            new Account(Name = 'Fidelity Partial Valid'),
            new Account()
        };
        Test.startTest();
        FidelityPartialSaveService.saveAccounts(records);
        Test.stopTest();
        System.assertEquals(
            1,
            [SELECT COUNT() FROM Account WHERE Name = 'Fidelity Partial Valid']
        );
    }""",
    "SF-FID-019": """    @IsTest
    static void verifiesUtcContractDate() {
        Datetime boundary = Datetime.newInstanceGmt(2026, 1, 1, 0, 30, 0);
        Test.startTest();
        Date result = FidelityRenewalDateService.renewalDate(boundary);
        Test.stopTest();
        System.assertEquals(Date.newInstance(2026, 1, 1), result);
    }""",
    "SF-FID-020": """    @IsTest
    static void verifiesReplayIsIdempotent() {
        Map<String, Object> eventRecord = new Map<String, Object>{
            'eventUuid' => 'evt-fidelity-020',
            'subject' => 'Fidelity replay'
        };
        Test.startTest();
        FidelityEventConsumer.consume(
            new List<Map<String, Object>>{eventRecord, eventRecord}
        );
        Test.stopTest();
        System.assertEquals(
            1,
            [SELECT COUNT() FROM Case
             WHERE External_Event_Id__c = 'evt-fidelity-020']
        );
    }""",
}


SUPPORT_FILES: dict[str, dict[str, str]] = {
    "SF-FID-004": {
        "triggers/AccountAfterUpdate.trigger": """trigger AccountAfterUpdate on Account (after update) {
    FidelityRecursiveAccountHandler.afterUpdate(Trigger.new);
}""",
        "triggers/AccountAfterUpdate.trigger-meta.xml": trigger_meta(),
    },
    "SF-FID-007": {
        "objects/Contact/fields/SSN__c.field-meta.xml": custom_field(
            "SSN__c", "SSN", "Text", length=11
        ),
    },
    "SF-FID-008": {
        "objects/Opportunity/fields/Discount_Approved__c.field-meta.xml": custom_field(
            "Discount_Approved__c", "Discount Approved", "Checkbox"
        ),
        "objects/Opportunity/fields/Approval_Context__c.field-meta.xml": custom_field(
            "Approval_Context__c", "Approval Context", "Text", length=80
        ),
        "objects/Opportunity/validationRules/Require_Approval_Context.validationRule-meta.xml": """<?xml version="1.0" encoding="UTF-8"?>
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <errorConditionFormula>AND(Discount_Approved__c, ISBLANK(Approval_Context__c))</errorConditionFormula>
    <errorMessage>Approval context is required.</errorMessage>
</ValidationRule>""",
    },
    "SF-FID-009": {
        "classes/FidelityOwnerAssignmentJob.cls": """public with sharing class FidelityOwnerAssignmentJob implements Queueable {
    private Id accountId;
    private Id ownerId;

    public FidelityOwnerAssignmentJob(Account accountRecord) {
        accountId = accountRecord.Id;
        ownerId = accountRecord.OwnerId;
    }

    public void execute(QueueableContext context) {
        update new Account(Id = accountId, OwnerId = ownerId);
    }
}""",
        "classes/FidelityOwnerAssignmentJob.cls-meta.xml": apex_meta(),
    },
    "SF-FID-010": {
        "classes/InvoiceGatewayClient.cls": """public with sharing class InvoiceGatewayClient {
    public static HttpResponse send(Id opportunityId) {
        HttpRequest request = new HttpRequest();
        request.setEndpoint('callout:InvoiceGateway/invoices');
        request.setMethod('POST');
        request.setBody(JSON.serialize(new Map<String, Object>{'opportunityId' => opportunityId}));
        return new Http().send(request);
    }
}""",
        "classes/InvoiceGatewayClient.cls-meta.xml": apex_meta(),
    },
    "SF-FID-015": {
        "classes/FidelityCreditDecisionServiceStub.cls": """public class FidelityCreditDecisionServiceStub {
    public FidelityCreditDecisionServiceStub() {
    }
}""",
        "classes/FidelityCreditDecisionServiceStub.cls-meta.xml": apex_meta(),
    },
    "SF-FID-020": {
        "objects/Case/fields/External_Event_Id__c.field-meta.xml": custom_field(
            "External_Event_Id__c",
            "External Event Id",
            "Text",
            length=80,
            unique=True,
            external_id=True,
        ),
    },
}


REPLAY_ADAPTER = """public with sharing class FidelityBitemporalReplayAdapter {
    public class ReplayResult {
        @AuraEnabled public Boolean driftDetected;
        @AuraEnabled public String member;
        @AuraEnabled public String permission;
        @AuraEnabled public Datetime validTime;
        @AuraEnabled public Datetime transactionTime;
    }

    @AuraEnabled
    public static ReplayResult compare(String auditJson, String githubJson) {
        Map<String, Object> audit =
            (Map<String, Object>) JSON.deserializeUntyped(auditJson);
        Map<String, Object> github =
            (Map<String, Object>) JSON.deserializeUntyped(githubJson);
        ReplayResult result = new ReplayResult();
        result.member = String.valueOf(audit.get('member'));
        result.permission = String.valueOf(audit.get('permission'));
        result.validTime = Datetime.valueOf(
            String.valueOf(audit.get('valid_time')).replace('T', ' ').replace('Z', '')
        );
        result.transactionTime = Datetime.valueOf(
            String.valueOf(github.get('transaction_time')).replace('T', ' ').replace('Z', '')
        );
        result.driftDetected =
            String.valueOf(audit.get('new_value')) != String.valueOf(github.get('value'));
        return result;
    }
}"""


REPLAY_TEST = """@IsTest
private class FidelityBenchmark017Test {
    @IsTest
    static void verifiesDeterministicReplayComparison() {
        String audit =
            '{"member":"Finance Analyst","permission":"Financial_Dashboard__c.read",' +
            '"new_value":false,"valid_time":"2026-07-23T08:15:00Z"}';
        String github =
            '{"member":"Finance Analyst","permission":"Financial_Dashboard__c.read",' +
            '"value":true,"transaction_time":"2026-07-23T07:55:00Z"}';
        FidelityBitemporalReplayAdapter.ReplayResult result =
            FidelityBitemporalReplayAdapter.compare(audit, github);
        System.assertEquals(true, result.driftDetected);
        System.assertNotEquals(result.validTime, result.transactionTime);
        List<ObjectPermissions> permissions = [
            SELECT PermissionsRead
            FROM ObjectPermissions
            WHERE SObjectType = 'Financial_Dashboard__c'
            AND Parent.Profile.Name = 'Finance Analyst'
        ];
        System.assertEquals(1, permissions.size());
        System.assertEquals(true, permissions[0].PermissionsRead);
    }
}"""


SCENARIO_BODIES: dict[str, tuple[str, str]] = {
    "SF-FID-001": (
        """List<Account> records = new List<Account>();
        for (Integer i = 0; i < 101; i++) {
            records.add(new Account(Name = 'Fidelity UI Direct ' + i));
        }
        insert records;
        return new Map<String, Object>{'accountIds' => new Map<Id, Account>(records).keySet()};""",
        """List<Account> records = [
            SELECT Id, Name FROM Account WHERE Name LIKE 'Fidelity UI Direct %'
        ];
        Integer beforeQueries = Limits.getQueries();
        Map<Id, Integer> counts = FidelityDirectQueryService.contactCounts(records);
        return new Map<String, Object>{
            'recordCount' => records.size(),
            'resultCount' => counts.size(),
            'queryDelta' => Limits.getQueries() - beforeQueries
        };""",
    ),
    "SF-FID-002": (
        """Account parent = new Account(Name = 'Fidelity UI DML');
        insert parent;
        List<Opportunity> records = new List<Opportunity>();
        for (Integer i = 0; i < 151; i++) {
            records.add(new Opportunity(
                AccountId = parent.Id,
                Name = 'Fidelity UI Opportunity ' + i,
                StageName = 'Prospecting',
                CloseDate = Date.today().addDays(30)
            ));
        }
        insert records;
        return new Map<String, Object>{
            'accountId' => parent.Id,
            'opportunityIds' => new Map<Id, Opportunity>(records).keySet()
        };""",
        """List<Opportunity> records = [
            SELECT Id, StageName, CloseDate
            FROM Opportunity WHERE Name LIKE 'Fidelity UI Opportunity %'
        ];
        Integer beforeDml = Limits.getDmlStatements();
        FidelityDmlLoopService.closeWon(records);
        return new Map<String, Object>{
            'recordCount' => records.size(),
            'dmlDelta' => Limits.getDmlStatements() - beforeDml,
            'firstStage' => records[0].StageName
        };""",
    ),
    "SF-FID-003": (
        """List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 200; i++) {
            accounts.add(new Account(Name = 'Fidelity UI Quadratic ' + i));
        }
        insert accounts;
        List<Contact> contacts = new List<Contact>();
        for (Account accountRecord : accounts) {
            contacts.add(new Contact(
                AccountId = accountRecord.Id,
                LastName = accountRecord.Name
            ));
        }
        insert contacts;
        return new Map<String, Object>{
            'accountIds' => new Map<Id, Account>(accounts).keySet()
        };""",
        """List<Account> accounts = [
            SELECT Id FROM Account WHERE Name LIKE 'Fidelity UI Quadratic %'
        ];
        Set<Id> accountIds = new Map<Id, Account>(accounts).keySet();
        List<Contact> contacts = [
            SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds
        ];
        Integer beforeCpu = Limits.getCpuTime();
        Map<Id, Integer> scores =
            FidelityHiddenQuadraticService.scoreAccounts(accounts, contacts);
        return new Map<String, Object>{
            'accountCount' => accounts.size(),
            'contactCount' => contacts.size(),
            'resultCount' => scores.size(),
            'cpuMs' => Limits.getCpuTime() - beforeCpu
        };""",
    ),
    "SF-FID-004": (
        """Account record = new Account(Name = 'Fidelity UI Recursion');
        insert record;
        return new Map<String, Object>{'accountId' => record.Id};""",
        """Account record = [
            SELECT Id, Name FROM Account WHERE Name = 'Fidelity UI Recursion' LIMIT 1
        ];
        record.Name = 'Fidelity UI Recursion Updated';
        update record;
        Account actual = [SELECT Description FROM Account WHERE Id = :record.Id];
        return new Map<String, Object>{'description' => actual.Description};""",
    ),
    "SF-FID-005": (
        """Account record = new Account(Name = 'Fidelity UI Null Guard');
        insert record;
        return new Map<String, Object>{'accountId' => record.Id};""",
        """Integer beforeQueries = Limits.getQueries();
        String exceptionType;
        try {
            FidelityNullGuardController.loadAccount(null);
        } catch (Exception error) {
            exceptionType = error.getTypeName();
        }
        return new Map<String, Object>{
            'exceptionType' => exceptionType,
            'queryDelta' => Limits.getQueries() - beforeQueries
        };""",
    ),
    "SF-FID-006": (
        """Account record =
            new Account(Name = 'Fidelity UI Revenue', AnnualRevenue = 250000);
        insert record;
        return new Map<String, Object>{'accountIds' => new List<Id>{record.Id}};""",
        """Account record = [
            SELECT Id FROM Account WHERE Name = 'Fidelity UI Revenue' LIMIT 1
        ];
        List<Account> result =
            FidelityRevenueController.loadRevenue(new Set<Id>{record.Id});
        return new Map<String, Object>{
            'resultCount' => result.size(),
            'annualRevenue' => result.isEmpty() ? null : result[0].AnnualRevenue
        };""",
    ),
    "SF-FID-007": (
        """return new Map<String, Object>();""",
        """List<FieldPermissions> permissions = [
            SELECT Field, PermissionsRead, Parent.Name
            FROM FieldPermissions
            WHERE Field = 'Contact.SSN__c' AND Parent.Name = 'Guest Checkout'
        ];
        return new Map<String, Object>{
            'rowCount' => permissions.size(),
            'permissionsRead' =>
                permissions.isEmpty() ? null : permissions[0].PermissionsRead
        };""",
    ),
    "SF-FID-008": (
        """Account parent = new Account(Name = 'Fidelity UI Flow');
        insert parent;
        Opportunity record = new Opportunity(
            AccountId = parent.Id,
            Name = 'Fidelity UI Discount',
            StageName = 'Prospecting',
            CloseDate = Date.today().addDays(30)
        );
        insert record;
        return new Map<String, Object>{'opportunityId' => record.Id};""",
        """Opportunity record = [
            SELECT Id, Description FROM Opportunity
            WHERE Name = 'Fidelity UI Discount' LIMIT 1
        ];
        record.Description = 'Trigger approval';
        update record;
        Opportunity actual = [
            SELECT Discount_Approved__c, Approval_Context__c
            FROM Opportunity WHERE Id = :record.Id
        ];
        return new Map<String, Object>{
            'discountApproved' => actual.Discount_Approved__c,
            'approvalContext' => actual.Approval_Context__c
        };""",
    ),
    "SF-FID-009": (
        """Account record = new Account(Name = 'Fidelity UI Mixed DML');
        insert record;
        return new Map<String, Object>{'accountId' => record.Id};""",
        """Account record = [
            SELECT Id, OwnerId FROM Account WHERE Name = 'Fidelity UI Mixed DML' LIMIT 1
        ];
        User owner = [SELECT Id, IsActive FROM User WHERE Id = :UserInfo.getUserId()];
        FidelityMixedDmlService.activateOwner(owner, record);
        return new Map<String, Object>{
            'accountId' => record.Id,
            'requestedOwnerId' => owner.Id,
            'asyncVerificationRequired' => true
        };""",
    ),
    "SF-FID-010": (
        """Opportunity record = new Opportunity(
            Name = 'Fidelity UI Invoice',
            StageName = 'Prospecting',
            CloseDate = Date.today().addDays(30)
        );
        insert record;
        return new Map<String, Object>{'opportunityId' => record.Id};""",
        """Opportunity record = [
            SELECT Id, Description FROM Opportunity
            WHERE Name = 'Fidelity UI Invoice' LIMIT 1
        ];
        HttpResponse response = FidelityInvoiceCalloutService.sendInvoice(record);
        return new Map<String, Object>{
            'statusCode' => response.getStatusCode(),
            'description' => [
                SELECT Description FROM Opportunity WHERE Id = :record.Id
            ].Description
        };""",
    ),
    "SF-FID-011": (
        """Account parent = new Account(Name = 'Fidelity UI Timeline');
        insert parent;
        List<Task> records = new List<Task>();
        for (Integer i = 0; i < 201; i++) {
            records.add(new Task(
                WhatId = parent.Id,
                Subject = 'Fidelity UI Activity ' + i,
                Status = 'Not Started',
                Priority = 'Normal'
            ));
        }
        insert records;
        return new Map<String, Object>{'accountId' => parent.Id};""",
        """Id accountId = [
            SELECT Id FROM Account WHERE Name = 'Fidelity UI Timeline' LIMIT 1
        ].Id;
        List<Task> result =
            FidelityActivityTimelineController.loadTimeline(accountId);
        return new Map<String, Object>{'timelineCount' => result.size()};""",
    ),
    "SF-FID-012": (
        """insert new List<Account>{
            new Account(Name = 'Fidelity UI Search Alpha'),
            new Account(Name = 'Fidelity UI Search Beta')
        };
        return new Map<String, Object>{
            'normalizedSearchTerm' => '%Fidelity UI Search%'
        };""",
        """List<Account> result =
            FidelityAccountSearchController.search('%\\' OR Name != \\'');
        return new Map<String, Object>{'resultCount' => result.size()};""",
    ),
    "SF-FID-013": (
        """Account record = new Account(Name = 'Fidelity UI Original');
        insert record;
        return new Map<String, Object>{'accountId' => record.Id};""",
        """Account record = [
            SELECT Id, Name FROM Account WHERE Name = 'Fidelity UI Original' LIMIT 1
        ];
        record.Name = 'Fidelity UI Renamed';
        FidelityOptimisticLockService.renameAccount(record);
        return new Map<String, Object>{
            'name' => [SELECT Name FROM Account WHERE Id = :record.Id].Name
        };""",
    ),
    "SF-FID-014": (
        """Case record = new Case(
            Subject = 'Fidelity UI Export',
            Origin = 'Web'
        );
        insert record;
        return new Map<String, Object>{'caseId' => record.Id};""",
        """List<Case> result = FidelityCaseExportController.exportOpenCases();
        return new Map<String, Object>{'resultCount' => result.size()};""",
    ),
    "SF-FID-015": (
        """Account record = new Account(
            Name = 'Fidelity UI Credit',
            Jataka_Credit_Score__c = 550,
            Rating = 'Warm'
        );
        insert record;
        return new Map<String, Object>{'accountId' => record.Id};""",
        """Account record = [
            SELECT Id FROM Account WHERE Name = 'Fidelity UI Credit' LIMIT 1
        ];
        FidelityCreditAction.Input input = new FidelityCreditAction.Input();
        input.accountId = record.Id;
        FidelityCreditAction.evaluate(new List<FidelityCreditAction.Input>{input});
        Account actual = [
            SELECT Jataka_Credit_Score__c, Rating FROM Account WHERE Id = :record.Id
        ];
        return new Map<String, Object>{
            'creditScore' => actual.Jataka_Credit_Score__c,
            'rating' => actual.Rating
        };""",
    ),
    "SF-FID-016": (
        """List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 101; i++) {
            accounts.add(new Account(Name = 'Fidelity UI Large ' + i));
        }
        insert accounts;
        List<Opportunity> opportunities = new List<Opportunity>();
        for (Account accountRecord : accounts) {
            opportunities.add(new Opportunity(
                AccountId = accountRecord.Id,
                Name = 'Fidelity UI Invoice ' + accountRecord.Id,
                Amount = 10,
                StageName = 'Prospecting',
                CloseDate = Date.today().addDays(30)
            ));
        }
        insert opportunities;
        return new Map<String, Object>{
            'accountIds' => new Map<Id, Account>(accounts).keySet()
        };""",
        """List<Account> accounts = [
            SELECT Id FROM Account WHERE Name LIKE 'Fidelity UI Large %'
        ];
        Map<Id, Decimal> result =
            FidelityLargeInvoiceService.calculateTotals(accounts);
        return new Map<String, Object>{
            'accountCount' => accounts.size(),
            'resultCount' => result.size(),
            'sampleTotal' => result.get(accounts[0].Id)
        };""",
    ),
    "SF-FID-017": (
        """return new Map<String, Object>();""",
        """String audit =
            '{"member":"Finance Analyst","permission":"Financial_Dashboard__c.read",' +
            '"new_value":false,"valid_time":"2026-07-23T08:15:00Z"}';
        String github =
            '{"member":"Finance Analyst","permission":"Financial_Dashboard__c.read",' +
            '"value":true,"transaction_time":"2026-07-23T07:55:00Z"}';
        FidelityBitemporalReplayAdapter.ReplayResult comparison =
            FidelityBitemporalReplayAdapter.compare(audit, github);
        List<ObjectPermissions> permissions = [
            SELECT PermissionsRead
            FROM ObjectPermissions
            WHERE SObjectType = 'Financial_Dashboard__c'
            AND Parent.Profile.Name = 'Finance Analyst'
        ];
        return new Map<String, Object>{
            'driftDetected' => comparison.driftDetected,
            'validTime' => comparison.validTime,
            'transactionTime' => comparison.transactionTime,
            'remediatedRead' =>
                permissions.isEmpty() ? null : permissions[0].PermissionsRead,
            'externalPipelineEvidenceRequired' => true
        };""",
    ),
    "SF-FID-018": (
        """return new Map<String, Object>();""",
        """List<Account> records = new List<Account>{
            new Account(Name = 'Fidelity UI Partial Valid'),
            new Account()
        };
        FidelityPartialSaveService.saveAccounts(records);
        return new Map<String, Object>{
            'persistedCount' => [
                SELECT COUNT() FROM Account
                WHERE Name = 'Fidelity UI Partial Valid'
            ]
        };""",
    ),
    "SF-FID-019": (
        """Account parent = new Account(Name = 'Fidelity UI Contract');
        insert parent;
        Contract record = new Contract(
            AccountId = parent.Id,
            StartDate = Date.newInstance(2026, 1, 1),
            ContractTerm = 12,
            Status = 'Draft'
        );
        insert record;
        return new Map<String, Object>{'contractId' => record.Id};""",
        """Datetime boundary = Datetime.newInstanceGmt(2026, 1, 1, 0, 30, 0);
        return new Map<String, Object>{
            'renewalDate' => FidelityRenewalDateService.renewalDate(boundary),
            'expectedUtcDate' => Date.newInstance(2026, 1, 1)
        };""",
    ),
    "SF-FID-020": (
        """return new Map<String, Object>{'eventUuid' => 'evt-fidelity-ui-020'};""",
        """Map<String, Object> eventRecord = new Map<String, Object>{
            'eventUuid' => 'evt-fidelity-ui-020',
            'subject' => 'Fidelity UI replay'
        };
        FidelityEventConsumer.consume(
            new List<Map<String, Object>>{eventRecord, eventRecord}
        );
        return new Map<String, Object>{
            'persistedCount' => [
                SELECT COUNT() FROM Case
                WHERE External_Event_Id__c = 'evt-fidelity-ui-020'
            ]
        };""",
    ),
}


def scenario_class(seed_body: str, run_body: str) -> str:
    return f"""global with sharing class FidelityBenchmarkScenario {{
    global static Map<String, Object> seed() {{
        {seed_body}
    }}

    global static Map<String, Object> run() {{
        {run_body}
    }}
}}"""


HARNESS_CONTROLLER = """global with sharing class FidelityBenchmarkHarnessController {
    @RemoteAction
    global static String run() {
        Map<String, Object> observation = FidelityBenchmarkScenario.run();
        observation.put('observedAt', Datetime.now().formatGmt('yyyy-MM-dd\\'T\\'HH:mm:ss\\'Z\\''));
        return JSON.serialize(observation);
    }
}"""


def harness_page(case_id: str) -> str:
    return f"""<apex:page showHeader="true" sidebar="false">
    <apex:pageMessages />
    <h1>Jataka Salesforce Fidelity {case_id}</h1>
    <button data-jataka-case="{case_id}" data-action="run"
            type="button" onclick="runBenchmark()">Run benchmark</button>
    <pre data-jataka-case="{case_id}" data-result="">Not run</pre>
    <script>
    function runBenchmark() {{
        var resultNode = document.querySelector(
            '[data-jataka-case="{case_id}"][data-result]'
        );
        resultNode.textContent = 'RUNNING';
        Visualforce.remoting.Manager.invokeAction(
            '{{!$RemoteAction.FidelityBenchmarkHarnessController.run}}',
            function(result, event) {{
                resultNode.textContent = event.status
                    ? result
                    : JSON.stringify({{error: event.message}});
            }},
            {{escape: true}}
        );
    }}
    </script>
</apex:page>"""


def page_meta() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ApexPage xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>{API_VERSION}</apiVersion>
    <availableInTouch>true</availableInTouch>
    <confirmationTokenRequired>false</confirmationTokenRequired>
    <label>Fidelity Benchmark</label>
</ApexPage>"""


def fixture_target(relative: str) -> str | None:
    fixture = Path(relative)
    name = fixture.name
    if name.endswith(".cls") or name.endswith(".cls-meta.xml"):
        return f"classes/{name}"
    if name.endswith(".trigger") or name.endswith(".trigger-meta.xml"):
        return f"triggers/{name}"
    if name.endswith(".profile-meta.xml"):
        return f"profiles/{name}"
    if name.endswith(".flow-meta.xml"):
        return f"flows/{name}"
    if "/objects/" in f"/{relative}":
        return relative.split("/objects/", 1)[1].join(["objects/", ""])
    return None


def replace_managed_boundary(source: str) -> str:
    return source.replace(
        "Type.forName('ncino', 'CreditDecisionService')",
        "Type.forName('FidelityCreditDecisionServiceStub')",
    )


def source_adapter(case_id: str, target: str, source: str) -> tuple[str, dict[str, Any] | None]:
    if case_id == "SF-FID-015" and target == "classes/FidelityCreditAction.cls":
        adapted = replace_managed_boundary(source)
        return adapted, {
            "id": "local-managed-boundary",
            "kind": "managed_package_type_adapter",
            "description": (
                "The execution bundle substitutes a local Type.forName target so the "
                "managed-package transaction effect is reproducible without licensed IP."
            ),
            "original_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "adapted_sha256": hashlib.sha256(adapted.encode()).hexdigest(),
            "production_boundary_still_required": True,
        }
    if case_id == "SF-FID-015" and target == "flows/FidelityCreditReview.flow-meta.xml":
        adapted = source.replace(
            "<actionName>FidelityCreditAction.evaluate</actionName>",
            "<actionName>FidelityCreditAction</actionName>",
        )
        return adapted, {
            "id": "local-invocable-action-name",
            "kind": "flow_invocable_adapter",
            "description": (
                "The graph fixture retains its method-qualified semantic symbol; "
                "the deploy bundle uses Salesforce's class-qualified Apex action name."
            ),
            "original_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "adapted_sha256": hashlib.sha256(adapted.encode()).hexdigest(),
            "production_boundary_still_required": False,
        }
    return source, None


def query_engine(case: dict[str, Any]) -> str:
    action = case["verification"]["soql"]["actions"][0]
    return "cypher" if "MATCH (" in action else "soql"


def extract_query(case: dict[str, Any]) -> str:
    action = case["verification"]["soql"]["actions"][0]
    prefix = "Execute read-only SOQL: "
    statement = action[len(prefix) :] if action.startswith(prefix) else action
    if query_engine(case) == "soql":
        statement = re.sub(
            r":([A-Za-z_][A-Za-z0-9_]*)", r"${\1}", statement
        )
    return statement


def build_execution_bundles(
    root: Path,
    cases: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    execution_root = root / "execution"
    if execution_root.exists():
        shutil.rmtree(execution_root)
    results: dict[str, dict[str, Any]] = {}
    fulfilled_prerequisites = {
        "SF-FID-007": {"Contact.SSN__c encrypted text fixture"},
        "SF-FID-008": {
            "Opportunity.Discount_Approved__c",
            "Opportunity.Require_Approval_Context validation rule",
        },
        "SF-FID-015": {
            "A benchmark stub or licensed ncino.CreditDecisionService implementation"
        },
    }

    for case in cases:
        case_id = case["id"]
        bundle_root = execution_root / case_id
        package_root = bundle_root / "package" / "main" / "default"
        adaptations: list[dict[str, Any]] = []
        fixture_bindings: list[dict[str, Any]] = []

        for fixture in case["source"]["fixtures"]:
            target = fixture_target(fixture["path"])
            if target is None:
                continue
            source = (root / fixture["path"]).read_text(encoding="utf-8")
            source, adaptation = source_adapter(case_id, target, source)
            destination = package_root / target
            write_text(destination, source)
            fixture_bindings.append(
                {
                    "fixture": fixture["path"],
                    "fixture_sha256": fixture["sha256"],
                    "package_member": f"package/main/default/{target}",
                    "package_member_sha256": sha256_file(destination),
                }
            )
            if adaptation:
                adaptations.append(adaptation)

        for relative, content in SUPPORT_FILES.get(case_id, {}).items():
            write_text(package_root / relative, content)

        seed_body, run_body = SCENARIO_BODIES[case_id]
        harness_files = {
            "classes/FidelityBenchmarkScenario.cls": scenario_class(
                seed_body, run_body
            ),
            "classes/FidelityBenchmarkScenario.cls-meta.xml": apex_meta(),
            "classes/FidelityBenchmarkHarnessController.cls": HARNESS_CONTROLLER,
            "classes/FidelityBenchmarkHarnessController.cls-meta.xml": apex_meta(),
            "pages/FidelityBenchmark.page": harness_page(case_id),
            "pages/FidelityBenchmark.page-meta.xml": page_meta(),
        }
        for relative, content in harness_files.items():
            write_text(package_root / relative, content)
        write_text(
            bundle_root / "scripts" / "seed.apex",
            """Map<String, Object> bindings = FidelityBenchmarkScenario.seed();
System.debug(LoggingLevel.ERROR, 'JATAKA_BINDINGS=' + JSON.serialize(bindings));""",
        )

        apex_test_class: str | None = None
        if case_id in TEST_BODIES:
            apex_test_class, source = test_class(case_id, TEST_BODIES[case_id])
            write_text(package_root / "classes" / f"{apex_test_class}.cls", source)
            write_text(
                package_root / "classes" / f"{apex_test_class}.cls-meta.xml",
                apex_meta(),
            )
        elif case_id == "SF-FID-017":
            apex_test_class = "FidelityBenchmark017Test"
            write_text(
                package_root / "classes" / "FidelityBitemporalReplayAdapter.cls",
                REPLAY_ADAPTER,
            )
            write_text(
                package_root
                / "classes"
                / "FidelityBitemporalReplayAdapter.cls-meta.xml",
                apex_meta(),
            )
            write_text(
                package_root / "classes" / f"{apex_test_class}.cls", REPLAY_TEST
            )
            write_text(
                package_root / "classes" / f"{apex_test_class}.cls-meta.xml",
                apex_meta(),
            )

        special_generated = (
            [
                "classes/FidelityBitemporalReplayAdapter.cls",
                "classes/FidelityBitemporalReplayAdapter.cls-meta.xml",
            ]
            if case_id == "SF-FID-017"
            else []
        )
        generated_members = sorted(
            {
                f"package/main/default/{relative}"
                for relative in (
                    *SUPPORT_FILES.get(case_id, {}).keys(),
                    *harness_files.keys(),
                    *special_generated,
                    f"classes/{apex_test_class}.cls",
                    f"classes/{apex_test_class}.cls-meta.xml",
                )
            }
        )

        write_json(
            bundle_root / "sfdx-project.json",
            {
                "packageDirectories": [{"path": "package", "default": True}],
                "name": f"salesforce-fidelity-{case_id.lower()}",
                "namespace": "",
                "sfdcLoginUrl": "https://login.salesforce.com",
                "sourceApiVersion": API_VERSION,
            },
        )
        write_json(
            bundle_root / "config" / "project-scratch-def.json",
            {
                "orgName": f"Jataka Fidelity {case_id}",
                "edition": "Developer",
                "features": [],
                "settings": {
                    "lightningExperienceSettings": {
                        "enableS1DesktopEnabled": True
                    }
                },
            },
        )

        mode = (
            "event_replay_adapter"
            if case_id == "SF-FID-017"
            else "metadata_probe"
            if case_id == "SF-FID-007"
            else "deploy_and_test"
        )
        engine = query_engine(case)
        descriptor = {
            "schema_version": "1.0.0",
            "case_id": case_id,
            "mode": mode,
            "patch_contract": {
                "output_format": case["patch_contract"]["output_format"],
                "raw_text_forbidden": case["patch_contract"]["raw_text_forbidden"],
                "sha256": hashlib.sha256(
                    canonical_bytes(case["patch_contract"])
                ).hexdigest(),
            },
            "package": {
                "project_file": "sfdx-project.json",
                "source_root": "package",
                "api_version": API_VERSION,
                "fixture_bindings": fixture_bindings,
                "source_adapters": adaptations,
                "generated_members": [
                    {
                        "path": relative,
                        "sha256": sha256_file(bundle_root / relative),
                    }
                    for relative in generated_members
                ],
            },
            "apex": {
                "required": apex_test_class is not None,
                "test_class": apex_test_class,
                "test_level": "RunSpecifiedTests" if apex_test_class else None,
                "command": (
                    f"sf apex run test --tests {apex_test_class} "
                    "--result-format json --wait 20 --target-org ${TARGET_ORG}"
                    if apex_test_class
                    else None
                ),
                "assertions": case["verification"]["apex"]["assertions"],
            },
            "queries": [
                {
                    "id": f"{case_id.lower()}-postcondition",
                    "engine": engine,
                    "statement": extract_query(case),
                    "bindings": {
                        "source": "seed_command_stdout",
                        "marker": "JATAKA_BINDINGS=",
                        "syntax": "${bindingName}",
                        "renderer": "salesforce_soql_literal_v1",
                        "variables": sorted(
                            set(re.findall(r"\$\{([^}]+)\}", extract_query(case)))
                        ),
                    },
                    "read_only": True,
                    "assertions": case["verification"]["soql"]["assertions"],
                    "runner": {
                        "path": "../../tools/run_query.py",
                        "sha256": sha256_file(root / "tools" / "run_query.py"),
                        "command": (
                            "python3 ../../tools/run_query.py "
                            "--descriptor execution.json "
                            "--seed-result ${EVIDENCE_DIR}/seed-result.json "
                            "--target-org ${TARGET_ORG} "
                            "--output ${EVIDENCE_DIR}/query-result.json"
                        ),
                    },
                }
            ],
            "seed": {
                "script": "scripts/seed.apex",
                "script_sha256": sha256_file(bundle_root / "scripts" / "seed.apex"),
                "declared_bindings": sorted(
                    set(re.findall(r"\$\{([^}]+)\}", extract_query(case)))
                ),
                "command": (
                    "sf apex run --file scripts/seed.apex --json "
                    "--target-org ${TARGET_ORG} "
                    "> ${EVIDENCE_DIR}/seed-result.json"
                ),
                "output": {
                    "format": "salesforce_cli_json_log",
                    "marker": "JATAKA_BINDINGS=",
                    "value": "json_object",
                },
                "idempotency": (
                    "fresh_scratch_org_once_per_case"
                ),
            },
            "metadata_probe": (
                {
                    "required": True,
                    "engine": "soql",
                    "statement": (
                        "SELECT Field, PermissionsRead, Parent.Name "
                        "FROM FieldPermissions "
                        "WHERE Field = 'Contact.SSN__c' "
                        "AND Parent.Name = 'Guest Checkout'"
                    ),
                    "expected": {
                        "row_count": 1,
                        "PermissionsRead": False,
                    },
                    "command": (
                        "sf data query --query \"${STATEMENT}\" "
                        "--result-format json --target-org ${TARGET_ORG}"
                    ),
                }
                if case_id == "SF-FID-007"
                else None
            ),
            "browser": {
                "required": True,
                "runner": "playwright",
                "driver": "jataka.salesforce.case.v1",
                "driver_path": "../../tools/run_browser_case.mjs",
                "driver_sha256": sha256_file(
                    root / "tools" / "run_browser_case.mjs"
                ),
                "command": (
                    "node ../../tools/run_browser_case.mjs "
                    "--descriptor execution.json "
                    "--artifacts ${EVIDENCE_DIR}/playwright"
                ),
                "entrypoint": case_id,
                "base_url": "${SCRATCH_ORG_INSTANCE_URL}",
                "route": "/apex/FidelityBenchmark",
                "authentication": "sf_frontdoor_url",
                "inputs": {
                    "case_id": case_id,
                    "entry_symbol": case["source"]["entry_symbol"],
                    "seed_source": "seed_command_stdout",
                },
                "selectors": {
                    "action": f"[data-jataka-case='{case_id}'][data-action='run']",
                    "result": f"[data-jataka-case='{case_id}'][data-result]",
                },
                "scenario": {
                    "setup": case["verification"]["browser"]["setup"],
                    "actions": case["verification"]["browser"]["actions"],
                    "assertions": case["verification"]["browser"]["assertions"],
                },
                "artifacts": [
                    "playwright/trace.zip",
                    "playwright/video.webm",
                    "playwright/final-state.png",
                ],
            },
            "event_replay": (
                {
                    "adapter_class": "FidelityBitemporalReplayAdapter",
                    "inputs": [
                        {
                            "path": fixture["path"],
                            "sha256": fixture["sha256"],
                        }
                        for fixture in case["source"]["fixtures"]
                    ],
                    "external_stages": ["kafka", "temporal", "neo4j"],
                    "external_evidence_required": True,
                    "local_adapter_scope": (
                        "Validates payload parsing and bitemporal drift comparison only; "
                        "it cannot satisfy the streaming-pipeline release gate."
                    ),
                }
                if case_id == "SF-FID-017"
                else None
            ),
            "evidence": {
                "precomputed_results": False,
                "required": [
                    "deploy-result.json",
                    "apex-test-result.json" if apex_test_class else "metadata-probe.json",
                    "query-result.json",
                    "playwright/trace.zip",
                    "playwright/video.webm",
                    "playwright/final-state.png",
                    "cleanup-result.json",
                    "evidence-manifest.sha256",
                ],
                "pass_source": "observed_runtime_only",
            },
            "prerequisites": [
                "authenticated target scratch org",
                "AST compiler output bound to the source fixture SHA-256",
                "Jataka Playwright driver jataka.salesforce.case.v1",
                *[
                    prerequisite
                    for prerequisite in case["source"].get("prerequisites", [])
                    if prerequisite
                    not in fulfilled_prerequisites.get(case_id, set())
                ],
                *(
                    ["live ncino namespace for production-boundary fidelity"]
                    if case_id == "SF-FID-015"
                    else []
                ),
            ],
        }
        write_json(bundle_root / "execution.json", descriptor)

        governed = sorted(
            path.relative_to(bundle_root).as_posix()
            for path in bundle_root.rglob("*")
            if path.is_file() and path.name != "bundle.lock.json"
        )
        file_hashes = {
            relative: sha256_file(bundle_root / relative) for relative in governed
        }
        bundle_digest = hashlib.sha256(canonical_bytes(file_hashes)).hexdigest()
        write_json(
            bundle_root / "bundle.lock.json",
            {
                "schema_version": "1.0.0",
                "algorithm": "sha256",
                "bundle_sha256": bundle_digest,
                "files": file_hashes,
            },
        )
        results[case_id] = {
            "descriptor": f"execution/{case_id}/execution.json",
            "descriptor_sha256": sha256_file(bundle_root / "execution.json"),
            "bundle_lock": f"execution/{case_id}/bundle.lock.json",
            "bundle_sha256": bundle_digest,
            "mode": mode,
            "apex_test_class": apex_test_class,
        }

    return results
