public with sharing class FidelityDmlLoopService {
    public static void closeWon(List<Opportunity> opportunities) {
        for (Opportunity opportunityRecord : opportunities) {
            opportunityRecord.StageName = 'Closed Won';
            opportunityRecord.CloseDate = Date.today();
            update opportunityRecord;
        }
    }
}
