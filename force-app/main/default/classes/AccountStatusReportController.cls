public with sharing class AccountStatusReportController {
    @AuraEnabled(cacheable=true)
    public static Integer countByStatus(String statusValue) {
        if (String.isBlank(statusValue)) {
            return 0;
        }

        return [
            SELECT COUNT()
            FROM Account
            WHERE AccountStatus__c = :statusValue
        ];
    }
}
