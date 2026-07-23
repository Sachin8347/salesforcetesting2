@IsTest
private class FidelityBenchmark009Test {
    @IsTest
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
    }
}
