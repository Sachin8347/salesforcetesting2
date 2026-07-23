public with sharing class FidelityRecursiveAccountHandler {
    public static void afterUpdate(List<Account> records) {
        List<Account> pending = new List<Account>();
        for (Account accountRecord : records) {
            pending.add(new Account(Id = accountRecord.Id, Description = 'Normalized'));
        }
        if (!pending.isEmpty()) {
            update pending;
        }
    }
}
