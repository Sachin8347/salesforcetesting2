@IsTest
private class FidelityBenchmark004Test {
    @IsTest
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
    }
}
