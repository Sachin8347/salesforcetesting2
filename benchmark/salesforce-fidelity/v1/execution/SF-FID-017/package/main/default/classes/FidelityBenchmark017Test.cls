@IsTest
private class FidelityBenchmark017Test {
    @IsTest
    static void verifiesDeterministicReplayComparison() {
        String audit =
            '{"member":"Finance Analyst","permission":"Financial_Dashboard__c.read",' +
            '"new_value":false,"valid_time":"2026-07-23T08:15:00Z"}';
        String github =
            '{"member":"Finance Analyst","permission":"Financial_Dashboard__c.read",' +
            '"value":true,"transaction_time":"2026-07-23T07:55:00Z"}';
        FidelityBitemporalReplayAdapter.ReplayResult result =
            FidelityBitemporalReplayAdapter.compare(audit, github);
        System.assertEquals(true, result.driftDetected);
        System.assertNotEquals(result.validTime, result.transactionTime);
        List<ObjectPermissions> permissions = [
            SELECT PermissionsRead
            FROM ObjectPermissions
            WHERE SObjectType = 'Financial_Dashboard__c'
            AND Parent.Profile.Name = 'Finance Analyst'
        ];
        System.assertEquals(1, permissions.size());
        System.assertEquals(true, permissions[0].PermissionsRead);
    }
}
