@IsTest
private class FidelityBenchmark016Test {
    @IsTest
    static void verifiesAggregateTotals() {
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 101; i++) {
            accounts.add(new Account(Name = 'Fidelity Large ' + i));
        }
        insert accounts;
        List<Opportunity> opportunities = new List<Opportunity>();
        for (Account accountRecord : accounts) {
            opportunities.add(new Opportunity(
                AccountId = accountRecord.Id,
                Name = 'Fidelity Invoice ' + accountRecord.Name,
                Amount = 10,
                StageName = 'Prospecting',
                CloseDate = Date.today().addDays(30)
            ));
        }
        insert opportunities;
        Test.startTest();
        Map<Id, Decimal> totals =
            FidelityLargeInvoiceService.calculateTotals(accounts);
        Test.stopTest();
        System.assertEquals(10, totals.get(accounts[0].Id));
    }
}
