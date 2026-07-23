public with sharing class OpportunityReviewProbe {
    public static Map<Id, Integer> countLineItems(List<Opportunity> opportunities) {
        Map<Id, Integer> lineItemCounts = new Map<Id, Integer>();
        for (Opportunity opportunity : opportunities) {
            List<OpportunityLineItem> lineItems = [
                SELECT Id, OpportunityId
                FROM OpportunityLineItem
                WHERE OpportunityId = :opportunity.Id
            ];
            lineItemCounts.put(opportunity.Id, lineItems.size());
        }
        return lineItemCounts;
    }
}
