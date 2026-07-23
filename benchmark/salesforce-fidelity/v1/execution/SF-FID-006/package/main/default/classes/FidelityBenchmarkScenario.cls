global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        Account record =
            new Account(Name = 'Fidelity UI Revenue', AnnualRevenue = 250000);
        insert record;
        return new Map<String, Object>{'accountIds' => new List<Id>{record.Id}};
    }

    global static Map<String, Object> run() {
        Account record = [
            SELECT Id FROM Account WHERE Name = 'Fidelity UI Revenue' LIMIT 1
        ];
        List<Account> result =
            FidelityRevenueController.loadRevenue(new Set<Id>{record.Id});
        return new Map<String, Object>{
            'resultCount' => result.size(),
            'annualRevenue' => result.isEmpty() ? null : result[0].AnnualRevenue
        };
    }
}
