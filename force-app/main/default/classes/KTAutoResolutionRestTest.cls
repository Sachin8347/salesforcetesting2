@IsTest
private class KTAutoResolutionRestTest {
    @IsTest
    static void submitForReview_updatesStatusToPendingReview() {
        Knowledge_Translation_Request__c request = new Knowledge_Translation_Request__c(
            Language_Code__c = KnowledgeTranslationPublishService.LANG_SPANISH,
            Translation_Status__c = KnowledgeTranslationPublishService.STATUS_DRAFT,
            Assigned_Queue__c = KnowledgeTranslationPublishService.QUEUE_SPANISH
        );
        insert request;

        RestRequest req = new RestRequest();
        req.requestBody = Blob.valueOf(
            JSON.serialize(
                new Map<String, Object>{
                    'translationRequestId' => request.Id,
                    'operation' => 'submit_for_review'
                }
            )
        );
        RestContext.request = req;
        RestContext.response = new RestResponse();

        KnowledgeTranslationAutoResolutionRest.ActionResponse response =
            KnowledgeTranslationAutoResolutionRest.postAction();

        System.assertEquals(true, response.success);
        System.assertEquals(
            KnowledgeTranslationPublishService.STATUS_PENDING_REVIEW,
            response.translationStatus
        );

        Knowledge_Translation_Request__c refreshed = [
            SELECT Translation_Status__c
            FROM Knowledge_Translation_Request__c
            WHERE Id = :request.Id
            LIMIT 1
        ];
        System.assertEquals(
            KnowledgeTranslationPublishService.STATUS_PENDING_REVIEW,
            refreshed.Translation_Status__c
        );
    }

    @IsTest
    static void authorizePublication_requiresQueueMembership() {
        Knowledge_Translation_Request__c request = new Knowledge_Translation_Request__c(
            Language_Code__c = KnowledgeTranslationPublishService.LANG_SPANISH,
            Translation_Status__c = KnowledgeTranslationPublishService.STATUS_PENDING_REVIEW,
            Assigned_Queue__c = KnowledgeTranslationPublishService.QUEUE_SPANISH
        );
        insert request;

        RestRequest req = new RestRequest();
        req.requestBody = Blob.valueOf(
            JSON.serialize(
                new Map<String, Object>{
                    'translationRequestId' => request.Id,
                    'operation' => 'authorize_publication'
                }
            )
        );
        RestContext.request = req;
        RestContext.response = new RestResponse();

        Boolean threw = false;
        try {
            KnowledgeTranslationAutoResolutionRest.postAction();
        } catch (Exception e) {
            threw = true;
            System.assert(
                e.getMessage().contains('authorized') ||
                    e.getMessage().contains('member'),
                e.getMessage()
            );
        }
        System.assertEquals(true, threw, 'Expected queue authorization failure in test context.');
    }
}
