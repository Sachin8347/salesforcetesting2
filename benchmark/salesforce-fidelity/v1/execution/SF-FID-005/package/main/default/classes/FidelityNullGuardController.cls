public with sharing class FidelityNullGuardController {
    @AuraEnabled
    public static Account loadAccount(Id accountId) {
        return [SELECT Id, Name FROM Account WHERE Id = :accountId LIMIT 1];
    }
}
