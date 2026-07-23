public with sharing class OpportunityReviewProbe {
    public static Map<Id, Integer> countLineItems(List<Opportunity> opportunities) {
        Map<Id, Integer> lineItemCounts = new Map<Id, Integer>();
        Set<Id> opportunityIds = new Set<Id>();
        for (Opportunity opportunityForQuery : opportunities) {
            if (opportunityForQuery.Id != null) {
                opportunityIds.add(opportunityForQuery.Id);
            }
        }

        List<OpportunityLineItem> opportunityLineItemQueryResults = [
            SELECT Id, OpportunityId
            FROM OpportunityLineItem
            WHERE OpportunityId IN :opportunityIds
        ];
        Map<Id, List<OpportunityLineItem>> opportunityLineItemRecordsByOpportunityId = new Map<Id, List<OpportunityLineItem>>();
        for (OpportunityLineItem opportunityLineItemRecord : opportunityLineItemQueryResults) {
            if (!opportunityLineItemRecordsByOpportunityId.containsKey(opportunityLineItemRecord.OpportunityId)) {
                opportunityLineItemRecordsByOpportunityId.put(opportunityLineItemRecord.OpportunityId, new List<OpportunityLineItem>());
            }
            opportunityLineItemRecordsByOpportunityId.get(opportunityLineItemRecord.OpportunityId).add(opportunityLineItemRecord);
        }

        for (Opportunity opportunity : opportunities) {
            List<OpportunityLineItem> lineItems = opportunityLineItemRecordsByOpportunityId.get(opportunity.Id);
            if (lineItems == null) {
                lineItems = new List<OpportunityLineItem>();
            }
            lineItemCounts.put(opportunity.Id, lineItems.size());
        }
        return lineItemCounts;
    }
}
