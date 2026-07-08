public with sharing class AccountStatusService {
    public static final String STATUS_PENDING = 'Pending';
    public static final String STATUS_ACTIVE = 'Active';
    public static final String STATUS_BLOCKED = 'Blocked';

    public static void applyDefaultStatus(List<Account> accounts) {
        for (Account acc : accounts) {
            if (String.isBlank(acc.AccountStatus__c)) {
                acc.AccountStatus__c = STATUS_PENDING;
            }
        }
    }

    public static void markActiveWhenPhonePresent(List<Account> accounts) {
        for (Account acc : accounts) {
            if (!String.isBlank(acc.Phone)) {
                acc.AccountStatus__c = STATUS_ACTIVE;
            }
        }
    }
}
