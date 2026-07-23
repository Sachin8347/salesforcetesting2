public with sharing class FidelityOptimisticLockService {
    public static void renameAccount(Account detachedRecord) {
        update detachedRecord;
    }
}
