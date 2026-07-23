public with sharing class AccountProcessor {
    public static Map<Id, Integer> countContacts(List<Account> accounts) {
        Map<Id, Integer> contactCounts = new Map<Id, Integer>();

        for (Account account : accounts) {
            List<Contact> contacts = [
                SELECT Id, AccountId
                FROM Contact
                WHERE AccountId = :account.Id
            ];
            contactCounts.put(account.Id, contacts.size());
        }

        return contactCounts;
    }
}
