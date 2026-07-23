public with sharing class FidelityBitemporalReplayAdapter {
    public class ReplayResult {
        @AuraEnabled public Boolean driftDetected;
        @AuraEnabled public String member;
        @AuraEnabled public String permission;
        @AuraEnabled public Datetime validTime;
        @AuraEnabled public Datetime transactionTime;
    }

    @AuraEnabled
    public static ReplayResult compare(String auditJson, String githubJson) {
        Map<String, Object> audit =
            (Map<String, Object>) JSON.deserializeUntyped(auditJson);
        Map<String, Object> github =
            (Map<String, Object>) JSON.deserializeUntyped(githubJson);
        ReplayResult result = new ReplayResult();
        result.member = String.valueOf(audit.get('member'));
        result.permission = String.valueOf(audit.get('permission'));
        result.validTime = Datetime.valueOf(
            String.valueOf(audit.get('valid_time')).replace('T', ' ').replace('Z', '')
        );
        result.transactionTime = Datetime.valueOf(
            String.valueOf(github.get('transaction_time')).replace('T', ' ').replace('Z', '')
        );
        result.driftDetected =
            String.valueOf(audit.get('new_value')) != String.valueOf(github.get('value'));
        return result;
    }
}
