global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        Account record = new Account(Name = 'Fidelity UI Mixed DML');
        insert record;
        return new Map<String, Object>{'accountId' => record.Id};
    }

    global static Map<String, Object> run() {
        Account record = [
            SELECT Id, OwnerId FROM Account WHERE Name = 'Fidelity UI Mixed DML' LIMIT 1
        ];
        User owner = [SELECT Id, IsActive FROM User WHERE Id = :UserInfo.getUserId()];
        FidelityMixedDmlService.activateOwner(owner, record);
        return new Map<String, Object>{
            'accountId' => record.Id,
            'requestedOwnerId' => owner.Id,
            'asyncVerificationRequired' => true
        };
    }
}
