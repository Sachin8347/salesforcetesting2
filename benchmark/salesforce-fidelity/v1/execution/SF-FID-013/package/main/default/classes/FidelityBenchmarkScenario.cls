global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        Account record = new Account(Name = 'Fidelity UI Original');
        insert record;
        return new Map<String, Object>{'accountId' => record.Id};
    }

    global static Map<String, Object> run() {
        Account record = [
            SELECT Id, Name FROM Account WHERE Name = 'Fidelity UI Original' LIMIT 1
        ];
        record.Name = 'Fidelity UI Renamed';
        FidelityOptimisticLockService.renameAccount(record);
        return new Map<String, Object>{
            'name' => [SELECT Name FROM Account WHERE Id = :record.Id].Name
        };
    }
}
