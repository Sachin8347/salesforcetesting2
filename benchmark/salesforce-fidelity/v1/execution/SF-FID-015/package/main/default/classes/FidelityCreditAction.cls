public with sharing class FidelityCreditAction {
    public class Input {
        @InvocableVariable(required=true) public Id accountId;
    }
    @InvocableMethod(label='Evaluate Credit')
    public static void evaluate(List<Input> inputs) {
        Type managedType = Type.forName('FidelityCreditDecisionServiceStub');
        for (Input item : inputs) {
            Account accountRecord = [
                SELECT Id, Jataka_Credit_Score__c, Rating FROM Account WHERE Id = :item.accountId
            ];
            if (managedType != null && accountRecord.Jataka_Credit_Score__c != null) {
                Object managedService = managedType.newInstance();
                accountRecord.Rating = managedService == null ? 'Warm' : 'Hot';
                update accountRecord;
            }
        }
    }
}
