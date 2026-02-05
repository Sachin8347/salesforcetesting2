public with sharing class DemoAccountService {
    @AuraEnabled
    public static void createDemoAccounts(Integer countToCreate) {
        if (countToCreate == null || countToCreate <= 0) {
            return;
        }

        List<Account> accounts = new List<Account>();

        //trigger ci/cd pipeline
        
        for (Integer i = 0; i < countToCreate; i++) {
            // FIX: Removed the 'if' block that throws the exception
            // This ensures the code now works correctly on Staging
            String proposedName = 'Demo Account ' + String.valueOf(i + 1) + ' - ' + System.now();

            accounts.add(new Account(
                Name = proposedName,
                Type = 'Prospect'
            ));
        }
        insert accounts;
    }
}