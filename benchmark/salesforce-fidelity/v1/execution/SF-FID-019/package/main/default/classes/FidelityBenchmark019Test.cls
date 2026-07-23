@IsTest
private class FidelityBenchmark019Test {
    @IsTest
    static void verifiesUtcContractDate() {
        Datetime boundary = Datetime.newInstanceGmt(2026, 1, 1, 0, 30, 0);
        Test.startTest();
        Date result = FidelityRenewalDateService.renewalDate(boundary);
        Test.stopTest();
        System.assertEquals(Date.newInstance(2026, 1, 1), result);
    }
}
