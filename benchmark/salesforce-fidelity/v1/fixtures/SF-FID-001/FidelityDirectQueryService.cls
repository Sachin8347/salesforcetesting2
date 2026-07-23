public with sharing class FidelityDirectQueryService {
    public static Map<Id, Integer> contactCounts(List<Account> accounts) {
        Map<Id, Integer> result = new Map<Id, Integer>();
        for (Account accountRecord : accounts) {
            List<Contact> contacts = [
                SELECT Id, AccountId FROM Contact WHERE AccountId = :accountRecord.Id
            ];
            result.put(accountRecord.Id, contacts.size());
        }
        return result;
    }
}
