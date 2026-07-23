global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 101; i++) {
            accounts.add(new Account(Name = 'Fidelity UI Large ' + i));
        }
        insert accounts;
        List<Opportunity> opportunities = new List<Opportunity>();
        for (Account accountRecord : accounts) {
            opportunities.add(new Opportunity(
                AccountId = accountRecord.Id,
                Name = 'Fidelity UI Invoice ' + accountRecord.Id,
                Amount = 10,
                StageName = 'Prospecting',
                CloseDate = Date.today().addDays(30)
            ));
        }
        insert opportunities;
        return new Map<String, Object>{
            'accountIds' => new Map<Id, Account>(accounts).keySet()
        };
    }

    global static Map<String, Object> run() {
        List<Account> accounts = [
            SELECT Id FROM Account WHERE Name LIKE 'Fidelity UI Large %'
        ];
        Map<Id, Decimal> result =
            FidelityLargeInvoiceService.calculateTotals(accounts);
        return new Map<String, Object>{
            'accountCount' => accounts.size(),
            'resultCount' => result.size(),
            'sampleTotal' => result.get(accounts[0].Id)
        };
    }
}
