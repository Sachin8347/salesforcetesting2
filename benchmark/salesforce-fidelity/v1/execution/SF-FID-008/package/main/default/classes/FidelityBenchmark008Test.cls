@IsTest
private class FidelityBenchmark008Test {
    @IsTest
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
    }
}
