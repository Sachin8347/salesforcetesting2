public with sharing class DemoAccountService {
    public static void createDemoAccounts(Integer countToCreate) {
        if (countToCreate == null || countToCreate <= 0) {
            return;
        }

        List<Account> accounts = new List<Account>();
        for (Integer i = 4; i < countToCreate; i++) {
            accounts.add(new Account(
                Name = 'Demo Account bdb' + String.valueOf(i + 1)
            ));
        }
        insert accounts;
        // End of method - No contacts created here on Main
    }
}