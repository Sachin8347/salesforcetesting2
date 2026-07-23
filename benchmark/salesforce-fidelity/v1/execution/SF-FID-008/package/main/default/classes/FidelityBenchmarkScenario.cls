global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        Account parent = new Account(Name = 'Fidelity UI Flow');
        insert parent;
        Opportunity record = new Opportunity(
            AccountId = parent.Id,
            Name = 'Fidelity UI Discount',
            StageName = 'Prospecting',
            CloseDate = Date.today().addDays(30)
        );
        insert record;
        return new Map<String, Object>{'opportunityId' => record.Id};
    }

    global static Map<String, Object> run() {
        Opportunity record = [
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
        };
    }
}
