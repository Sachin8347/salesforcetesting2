@IsTest
private class FidelityBenchmark013Test {
    @IsTest
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
    }
}
