/**
 * REST entry point for Jataka auto-resolution to execute Salesforce Knowledge
 * translation state changes after human approval.
 */
@RestResource(urlMapping='/jataka/v1/knowledge-translation')
global with sharing class KnowledgeTranslationAutoResolutionRest {
    global class ActionRequest {
        public String translationRequestId;
        public String operation;
    }

    global class ActionResponse {
        public Boolean success;
        public String translationStatus;
        public String message;
        public String recordId;
        public String operation;
    }

    @HttpPost
    global static ActionResponse postAction() {
        ActionRequest body = (ActionRequest) JSON.deserialize(
            RestContext.request.requestBody.toString(),
            ActionRequest.class
        );

        if (String.isBlank(body.translationRequestId)) {
            throw new IllegalArgumentException('translationRequestId is required.');
        }
        if (String.isBlank(body.operation)) {
            throw new IllegalArgumentException('operation is required.');
        }

        Knowledge_Translation_Request__c updated;
        if (body.operation == 'submit_for_review') {
            updated = KnowledgeTranslationPublishService.submitForReview(
                body.translationRequestId
            );
        } else if (body.operation == 'authorize_publication') {
            Boolean isQueueMember = KnowledgeTranslationQueueHelper.isCurrentUserQueueMember(
                KnowledgeTranslationPublishService.LANG_SPANISH
            );
            updated = KnowledgeTranslationPublishService.authorizePublication(
                body.translationRequestId,
                isQueueMember
            );
        } else {
            throw new IllegalArgumentException(
                'Unsupported operation: ' + body.operation
            );
        }

        ActionResponse response = new ActionResponse();
        response.success = true;
        response.translationStatus = updated.Translation_Status__c;
        response.recordId = updated.Id;
        response.operation = body.operation;
        response.message =
            'Knowledge translation request updated to ' + updated.Translation_Status__c + '.';
        return response;
    }
}
