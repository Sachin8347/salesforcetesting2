/**
 * L1 entry point for Knowledge translation publish troubleshooting in MCP tests.
 */
public with sharing class KnowledgeTranslationPublishController {
    @AuraEnabled(cacheable=true)
    public static KnowledgeTranslationPublishService.PublishEligibilityResult checkPublishEligibility(
        Id translationRequestId
    ) {
        Knowledge_Translation_Request__c request = [
            SELECT Id, Language_Code__c, Translation_Status__c
            FROM Knowledge_Translation_Request__c
            WHERE Id = :translationRequestId
            LIMIT 1
        ];

        Boolean isQueueMember = KnowledgeTranslationQueueHelper.isCurrentUserQueueMember(
            request.Language_Code__c
        );

        return KnowledgeTranslationPublishService.evaluatePublishEligibility(request, isQueueMember);
    }

    @AuraEnabled
    public static Knowledge_Translation_Request__c submitSpanishDraftForReview(Id translationRequestId) {
        return KnowledgeTranslationPublishService.submitForReview(translationRequestId);
    }

    @AuraEnabled
    public static Knowledge_Translation_Request__c publishAfterQueueApproval(Id translationRequestId) {
        Boolean isQueueMember = KnowledgeTranslationQueueHelper.isCurrentUserQueueMember(
            KnowledgeTranslationPublishService.LANG_SPANISH
        );
        return KnowledgeTranslationPublishService.authorizePublication(
            translationRequestId,
            isQueueMember
        );
    }
}
