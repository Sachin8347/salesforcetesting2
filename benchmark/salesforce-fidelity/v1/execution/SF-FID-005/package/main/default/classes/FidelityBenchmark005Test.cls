@IsTest
private class FidelityBenchmark005Test {
    @IsTest
    static void verifiesNullGuardRunsBeforeQuery() {
        Integer beforeQueries = Limits.getQueries();
        try {
            FidelityNullGuardController.loadAccount(null);
            System.assert(false, 'Expected AuraHandledException');
        } catch (AuraHandledException expected) {
            System.assertEquals(beforeQueries, Limits.getQueries());
        }
    }
}
