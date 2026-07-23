@IsTest
private class FidelityBenchmark015Test {
    @IsTest
    static void verifiesLowScoreCannotBecomeHot() {
        Account accountRecord = new Account(
            Name = 'Fidelity Credit',
            Jataka_Credit_Score__c = 550,
            Rating = 'Warm'
        );
        insert accountRecord;
        FidelityCreditAction.Input input = new FidelityCreditAction.Input();
        input.accountId = accountRecord.Id;
        Test.startTest();
        FidelityCreditAction.evaluate(new List<FidelityCreditAction.Input>{input});
        Test.stopTest();
        System.assertEquals(
            'Warm',
            [SELECT Rating FROM Account WHERE Id = :accountRecord.Id].Rating
        );
    }
}
