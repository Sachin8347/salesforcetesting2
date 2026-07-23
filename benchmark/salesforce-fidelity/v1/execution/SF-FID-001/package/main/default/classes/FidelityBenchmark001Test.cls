@IsTest
private class FidelityBenchmark001Test {
    @IsTest
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
    }
}
