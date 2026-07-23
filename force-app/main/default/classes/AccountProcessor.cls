public with sharing class AccountProcessor {
    // Jataka branch synchronization probe.
    public static Map<Id, Integer> countContacts(List<Account> accounts) {
        Map<Id, Integer> contactCounts = new Map<Id, Integer>();

        Set<Id> accountIds = new Set<Id>();
        for (Account accountForQuery : accounts) {
            if (accountForQuery.Id != null) {
                accountIds.add(accountForQuery.Id);
            }
        }

        List<Contact> contactQueryResults = [
            SELECT Id, AccountId
            FROM Contact
            WHERE AccountId IN :accountIds
        ];
        Map<Id, List<Contact>> contactRecordsByAccountId = new Map<Id, List<Contact>>();
        for (Contact contactRecord : contactQueryResults) {
            if (!contactRecordsByAccountId.containsKey(contactRecord.AccountId)) {
                contactRecordsByAccountId.put(contactRecord.AccountId, new List<Contact>());
            }
            contactRecordsByAccountId.get(contactRecord.AccountId).add(contactRecord);
        }

        for (Account account : accounts) {
            List<Contact> contacts = contactRecordsByAccountId.get(account.Id);
            if (contacts == null) {
                contacts = new List<Contact>();
            }
            contactCounts.put(account.Id, contacts.size());
        }

        return contactCounts;
    }
}
