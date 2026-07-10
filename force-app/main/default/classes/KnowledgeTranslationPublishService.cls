/**
 * Encodes Salesforce Knowledge translation publishing rules for MCP L1/L2 consumer support.
 *
 * Platform behavior (ground truth for support answers):
 * - Salesforce Knowledge isolates publishing rights per language channel and article status.
 * - A greyed-out Publish button on a Spanish draft usually means the version is still in
 *   Draft Translations workflow, assigned to an explicit Translation Queue, or awaiting review.
 * - Knowledge Manager profile rights alone do NOT bypass per-language queue authorization.
 *
 * Resolution path for Spanish draft with Publish disabled:
 * 1. Confirm the translated version is assigned to a Translation Queue or validation step.
 * 2. Open Knowledge Articles tab and switch list view to "Draft Translations".
 * 3. Select the Spanish draft and use "Submit for Publication" or "Submit for Review".
 * 4. If the user is not in the Spanish translation group, a queue member must authorize publication.
 */
public with sharing class KnowledgeTranslationPublishService {
    public static final String STATUS_DRAFT = 'Draft';
    public static final String STATUS_IN_QUEUE = 'In_Translation_Queue';
    public static final String STATUS_PENDING_REVIEW = 'Pending_Review';
    public static final String STATUS_PUBLISHED = 'Published';

    public static final String LANG_ENGLISH = 'en_US';
    public static final String LANG_SPANISH = 'es';

    public static final String QUEUE_SPANISH = 'Spanish Translation Group';
    public static final String LIST_VIEW_DRAFT_TRANSLATIONS = 'Draft Translations';

    public class PublishEligibilityResult {
        @AuraEnabled public Boolean canPublishDirectly;
        @AuraEnabled public Boolean publishButtonEnabled;
        @AuraEnabled public String blockingReason;
        @AuraEnabled public String recommendedAction;
    }

    public static PublishEligibilityResult evaluatePublishEligibility(
        Knowledge_Translation_Request__c request,
        Boolean userIsSpanishQueueMember
    ) {
        PublishEligibilityResult result = new PublishEligibilityResult();
        result.canPublishDirectly = false;
        result.publishButtonEnabled = false;

        if (request == null) {
            result.blockingReason = 'Translation request not found.';
            result.recommendedAction = 'Open Draft Translations and select the Spanish draft.';
            return result;
        }

        if (request.Translation_Status__c == STATUS_PUBLISHED) {
            result.blockingReason = 'Article is already published for this language channel.';
            result.recommendedAction = 'No action required.';
            return result;
        }

        if (request.Translation_Status__c == STATUS_DRAFT
            || request.Translation_Status__c == STATUS_IN_QUEUE) {
            result.blockingReason = buildQueueBlockReason(request);
            result.recommendedAction =
                'Switch to list view "' + LIST_VIEW_DRAFT_TRANSLATIONS
                + '", select the Spanish draft, then Submit for Publication or Submit for Review.';
            return result;
        }

        if (request.Translation_Status__c == STATUS_PENDING_REVIEW) {
            if (request.Language_Code__c == LANG_SPANISH && !userIsSpanishQueueMember) {
                result.blockingReason =
                    'Spanish translation pending review. User is not a member of '
                    + String.valueOf(request.Assigned_Queue__c) + '.';
                result.recommendedAction =
                    'A designated member of the Spanish translation group must authorize publication.';
                return result;
            }

            result.canPublishDirectly = true;
            result.publishButtonEnabled = true;
            result.recommendedAction = 'Publish is available after queue review completes.';
            return result;
        }

        result.blockingReason = 'Unknown translation status: ' + request.Translation_Status__c;
        result.recommendedAction = 'Contact a Knowledge administrator.';
        return result;
    }

    public static Knowledge_Translation_Request__c submitForReview(Id requestId) {
        Knowledge_Translation_Request__c request = [
            SELECT Id, Language_Code__c, Translation_Status__c, Assigned_Queue__c
            FROM Knowledge_Translation_Request__c
            WHERE Id = :requestId
            LIMIT 1
        ];

        if (request.Translation_Status__c != STATUS_DRAFT
            && request.Translation_Status__c != STATUS_IN_QUEUE) {
            throw new IllegalArgumentException(
                'Only draft translations can be submitted. Current status: '
                + request.Translation_Status__c
            );
        }

        request.Translation_Status__c = STATUS_PENDING_REVIEW;
        if (String.isBlank(request.Assigned_Queue__c)
            && request.Language_Code__c == LANG_SPANISH) {
            request.Assigned_Queue__c = QUEUE_SPANISH;
        }

        update request;
        return request;
    }

    public static Knowledge_Translation_Request__c authorizePublication(
        Id requestId,
        Boolean authorizerIsQueueMember
    ) {
        Knowledge_Translation_Request__c request = [
            SELECT Id, Language_Code__c, Translation_Status__c, Assigned_Queue__c
            FROM Knowledge_Translation_Request__c
            WHERE Id = :requestId
            LIMIT 1
        ];

        if (request.Translation_Status__c != STATUS_PENDING_REVIEW) {
            throw new IllegalArgumentException(
                'Publication requires Pending Review status. Current status: '
                + request.Translation_Status__c
            );
        }

        if (request.Language_Code__c == LANG_SPANISH && !authorizerIsQueueMember) {
            throw new IllegalArgumentException(
                'User is not authorized to publish Spanish translations. '
                + 'A member of ' + request.Assigned_Queue__c + ' must approve.'
            );
        }

        request.Translation_Status__c = STATUS_PUBLISHED;
        update request;
        return request;
    }

    private static String buildQueueBlockReason(Knowledge_Translation_Request__c request) {
        String queueName = String.isBlank(request.Assigned_Queue__c)
            ? 'an explicit Translation Queue'
            : request.Assigned_Queue__c;

        return 'Publish is disabled: Salesforce Knowledge isolates publishing rights per language '
            + 'channel and article status. This ' + request.Language_Code__c
            + ' version is in "' + request.Translation_Status__c
            + '" and may be assigned to ' + queueName + '.';
    }
}
