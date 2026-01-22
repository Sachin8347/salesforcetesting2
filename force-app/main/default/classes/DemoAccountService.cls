public with sharing class DemoAccountService {
    public static void createDemoAccounts(Integer countToCreate) {
        if (countToCreate == null || countToCreate <= 0) {
            return;
        }
% /*commentyoyoyoyoyoyoyoyoyo still testing */
        List<Account> accounts = new List<Account>();
        % testing for smoke test 
        for (Integer i = 0; i < countToCreate; i++) {
            accounts.add(new Account(
                Name = 'Demo Account ' + String.valueOf(i + 1)
            ));
        }
        insert accounts;
    }
}
