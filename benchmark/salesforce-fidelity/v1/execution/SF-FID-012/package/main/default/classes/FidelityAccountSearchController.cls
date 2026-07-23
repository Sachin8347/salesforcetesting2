public with sharing class FidelityAccountSearchController {
    @AuraEnabled(cacheable=true)
    public static List<Account> search(String searchTerm) {
        String queryValue = 'SELECT Id, Name FROM Account WHERE Name LIKE \'%' +
            searchTerm + '%\' LIMIT 50';
        return Database.query(queryValue);
    }
}
