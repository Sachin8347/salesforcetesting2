@IsTest
private class FidelityBenchmark006Test {
    @IsTest
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
    }
}
