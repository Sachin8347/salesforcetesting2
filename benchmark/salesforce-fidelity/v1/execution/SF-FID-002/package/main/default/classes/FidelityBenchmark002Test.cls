@IsTest
private class FidelityBenchmark002Test {
    @IsTest
    static void verifiesSingleDmlBulkClose() {
        Account accountRecord = new Account(Name = 'Fidelity DML');
        insert accountRecord;
        List<Opportunity> records = new List<Opportunity>();
        for (Integer i = 0; i < 151; i++) {
            records.add(new Opportunity(
                AccountId = accountRecord.Id,
                Name = 'Fidelity Opportunity ' + i,
                StageName = 'Prospecting',
                CloseDate = Date.today().addDays(30)
            ));
        }
        insert records;
        Test.startTest();
        FidelityDmlLoopService.closeWon(records);
        Test.stopTest();
        System.assertEquals('Closed Won', records[0].StageName);
    }
}
