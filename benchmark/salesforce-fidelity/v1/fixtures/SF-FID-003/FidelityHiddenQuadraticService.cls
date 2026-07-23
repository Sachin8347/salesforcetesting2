public with sharing class FidelityHiddenQuadraticService {
    public static Map<Id, Integer> scoreAccounts(List<Account> accounts, List<Contact> contacts) {
        return dispatch(accounts, contacts);
    }
    private static Map<Id, Integer> dispatch(List<Account> accounts, List<Contact> contacts) {
        return calculate(accounts, contacts);
    }
    private static Map<Id, Integer> calculate(List<Account> accounts, List<Contact> contacts) {
        Map<Id, Integer> scores = new Map<Id, Integer>();
        for (Account accountRecord : accounts) {
            scores.put(accountRecord.Id, countMatches(accountRecord.Id, contacts));
        }
        return scores;
    }
    private static Integer countMatches(Id accountId, List<Contact> contacts) {
        Integer countValue = 0;
        for (Contact contactRecord : contacts) {
            if (contactRecord.AccountId == accountId) {
                countValue++;
            }
        }
        return countValue;
    }
}
