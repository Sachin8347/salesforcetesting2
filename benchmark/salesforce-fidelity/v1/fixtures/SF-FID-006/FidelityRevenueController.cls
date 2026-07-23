public with sharing class FidelityRevenueController {
    @AuraEnabled(cacheable=true)
    public static List<Account> loadRevenue(Set<Id> accountIds) {
        return [SELECT Id, Name, AnnualRevenue FROM Account WHERE Id IN :accountIds];
    }
}
