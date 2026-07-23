global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        Account parent = new Account(Name = 'Fidelity UI DML');
        insert parent;
        List<Opportunity> records = new List<Opportunity>();
        for (Integer i = 0; i < 151; i++) {
            records.add(new Opportunity(
                AccountId = parent.Id,
                Name = 'Fidelity UI Opportunity ' + i,
                StageName = 'Prospecting',
                CloseDate = Date.today().addDays(30)
            ));
        }
        insert records;
        return new Map<String, Object>{
            'accountId' => parent.Id,
            'opportunityIds' => new Map<Id, Opportunity>(records).keySet()
        };
    }

    global static Map<String, Object> run() {
        List<Opportunity> records = [
            SELECT Id, StageName, CloseDate
            FROM Opportunity WHERE Name LIKE 'Fidelity UI Opportunity %'
        ];
        Integer beforeDml = Limits.getDmlStatements();
        FidelityDmlLoopService.closeWon(records);
        return new Map<String, Object>{
            'recordCount' => records.size(),
            'dmlDelta' => Limits.getDmlStatements() - beforeDml,
            'firstStage' => records[0].StageName
        };
    }
}
