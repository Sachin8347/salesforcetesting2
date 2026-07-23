@IsTest
private class FidelityBenchmark018Test {
    @IsTest
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
    }
}
