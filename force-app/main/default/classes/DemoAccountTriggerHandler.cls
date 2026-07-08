public with sharing class DemoAccountTriggerHandler {
    public static void handleBeforeInsert(List<Account> newAccounts) {
        AccountStatusService.applyDefaultStatus(newAccounts);
        AccountStatusService.markActiveWhenPhonePresent(newAccounts);

        for (Account acc : newAccounts) {
            System.debug('Processing Account: ' + acc.Name + ' status=' + acc.AccountStatus__c);
        }
    }
}