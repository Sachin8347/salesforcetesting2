global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        List<Account> records = new List<Account>();
        for (Integer i = 0; i < 101; i++) {
            records.add(new Account(Name = 'Fidelity UI Direct ' + i));
        }
        insert records;
        return new Map<String, Object>{'accountIds' => new Map<Id, Account>(records).keySet()};
    }

    global static Map<String, Object> run() {
        List<Account> records = [
            SELECT Id, Name FROM Account WHERE Name LIKE 'Fidelity UI Direct %'
        ];
        Integer beforeQueries = Limits.getQueries();
        Map<Id, Integer> counts = FidelityDirectQueryService.contactCounts(records);
        return new Map<String, Object>{
            'recordCount' => records.size(),
            'resultCount' => counts.size(),
            'queryDelta' => Limits.getQueries() - beforeQueries
        };
    }
}
