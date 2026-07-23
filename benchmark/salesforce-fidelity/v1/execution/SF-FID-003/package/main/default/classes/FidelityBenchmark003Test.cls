@IsTest
private class FidelityBenchmark003Test {
    @IsTest
    static void verifiesIndexedScores() {
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 200; i++) {
            accounts.add(new Account(Name = 'Fidelity Quadratic ' + i));
        }
        insert accounts;
        List<Contact> contacts = new List<Contact>();
        for (Account accountRecord : accounts) {
            contacts.add(new Contact(
                AccountId = accountRecord.Id,
                LastName = accountRecord.Name
            ));
        }
        insert contacts;
        Test.startTest();
        Map<Id, Integer> scores =
            FidelityHiddenQuadraticService.scoreAccounts(accounts, contacts);
        Integer elapsed = Limits.getCpuTime();
        Test.stopTest();
        System.assertEquals(200, scores.size());
        System.assert(elapsed < 5000, 'Expected bounded CPU consumption');
    }
}
