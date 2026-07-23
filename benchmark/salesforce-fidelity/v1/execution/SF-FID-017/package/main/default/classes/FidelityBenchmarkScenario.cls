global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        return new Map<String, Object>();
    }

    global static Map<String, Object> run() {
        String audit =
            '{"member":"Finance Analyst","permission":"Financial_Dashboard__c.read",' +
            '"new_value":false,"valid_time":"2026-07-23T08:15:00Z"}';
        String github =
            '{"member":"Finance Analyst","permission":"Financial_Dashboard__c.read",' +
            '"value":true,"transaction_time":"2026-07-23T07:55:00Z"}';
        FidelityBitemporalReplayAdapter.ReplayResult comparison =
            FidelityBitemporalReplayAdapter.compare(audit, github);
        List<ObjectPermissions> permissions = [
            SELECT PermissionsRead
            FROM ObjectPermissions
            WHERE SObjectType = 'Financial_Dashboard__c'
            AND Parent.Profile.Name = 'Finance Analyst'
        ];
        return new Map<String, Object>{
            'driftDetected' => comparison.driftDetected,
            'validTime' => comparison.validTime,
            'transactionTime' => comparison.transactionTime,
            'remediatedRead' =>
                permissions.isEmpty() ? null : permissions[0].PermissionsRead,
            'externalPipelineEvidenceRequired' => true
        };
    }
}
