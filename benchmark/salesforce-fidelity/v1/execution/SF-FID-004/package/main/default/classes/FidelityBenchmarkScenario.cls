global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        Account record = new Account(Name = 'Fidelity UI Recursion');
        insert record;
        return new Map<String, Object>{'accountId' => record.Id};
    }

    global static Map<String, Object> run() {
        Account record = [
            SELECT Id, Name FROM Account WHERE Name = 'Fidelity UI Recursion' LIMIT 1
        ];
        record.Name = 'Fidelity UI Recursion Updated';
        update record;
        Account actual = [SELECT Description FROM Account WHERE Id = :record.Id];
        return new Map<String, Object>{'description' => actual.Description};
    }
}
