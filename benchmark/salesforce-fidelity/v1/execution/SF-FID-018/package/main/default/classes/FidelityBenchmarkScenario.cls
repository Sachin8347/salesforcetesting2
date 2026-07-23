global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        return new Map<String, Object>();
    }

    global static Map<String, Object> run() {
        List<Account> records = new List<Account>{
            new Account(Name = 'Fidelity UI Partial Valid'),
            new Account()
        };
        FidelityPartialSaveService.saveAccounts(records);
        return new Map<String, Object>{
            'persistedCount' => [
                SELECT COUNT() FROM Account
                WHERE Name = 'Fidelity UI Partial Valid'
            ]
        };
    }
}
