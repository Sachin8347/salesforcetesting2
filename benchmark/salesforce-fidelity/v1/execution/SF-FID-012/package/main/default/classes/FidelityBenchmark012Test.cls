@IsTest
private class FidelityBenchmark012Test {
    @TestSetup
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
            FidelityAccountSearchController.search('%\' OR Name != \'');
        Test.stopTest();
        System.assertEquals(0, result.size());
    }
}
