global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        Account record = new Account(
            Name = 'Fidelity UI Credit',
            Jataka_Credit_Score__c = 550,
            Rating = 'Warm'
        );
        insert record;
        return new Map<String, Object>{'accountId' => record.Id};
    }

    global static Map<String, Object> run() {
        Account record = [
            SELECT Id FROM Account WHERE Name = 'Fidelity UI Credit' LIMIT 1
        ];
        FidelityCreditAction.Input input = new FidelityCreditAction.Input();
        input.accountId = record.Id;
        FidelityCreditAction.evaluate(new List<FidelityCreditAction.Input>{input});
        Account actual = [
            SELECT Jataka_Credit_Score__c, Rating FROM Account WHERE Id = :record.Id
        ];
        return new Map<String, Object>{
            'creditScore' => actual.Jataka_Credit_Score__c,
            'rating' => actual.Rating
        };
    }
}
