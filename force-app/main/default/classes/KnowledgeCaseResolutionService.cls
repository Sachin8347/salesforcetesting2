/**
 * Encodes Salesforce Knowledge + Case console guidance for MCP L1/L2 consumer support.
 *
 * Platform behavior (ground truth for support answers):
 * - Agents attach Knowledge articles to the active Case from the Service Console
 *   Knowledge / Articles component (or Case Articles related list).
 * - Attaching creates a CaseArticle association so the article is tracked in
 *   resolution / Knowledge usage metrics and reporting.
 * - To send article text to the customer, open the console Email composer on the
 *   Case and Insert / Share Knowledge (or paste the customer-visible article body).
 * - Internal-only articles must NOT be emailed externally unless the article
 *   channel / visibility permits customer sharing.
 *
 * L1 resolution path (how-to — answer only):
 * 1. Open the active Case in Service Console.
 * 2. Use the Knowledge / Articles component (or Case Articles related list) to
 *    associate the internal article to the Case for metrics tracking.
 * 3. Open Email in the console and insert the article content/snippet/link into
 *    the customer email body, then send.
 * 4. If Insert Knowledge is unavailable, confirm the article is published to a
 *    customer-visible channel (not Internal App only).
 *
 * DATA_ACTION path (imperative — human approval required):
 * - "Attach article X to Case Y and send it now" is a mutation request, not L1 how-to.
 */
public with sharing class KnowledgeCaseResolutionService {
    public static final String COMPONENT_KNOWLEDGE = 'Knowledge';
    public static final String COMPONENT_ARTICLES = 'Articles';
    public static final String RELATED_LIST_CASE_ARTICLES = 'Case Articles';
    public static final String CONSOLE_EMAIL_COMPOSER = 'Email';
    public static final String ACTION_INSERT_KNOWLEDGE = 'Insert Knowledge';
    public static final String ACTION_SHARE_ARTICLE = 'Share Article';

    public static final String CHANNEL_INTERNAL = 'InternalApp';
    public static final String CHANNEL_CUSTOMER = 'Customer';
    public static final String CHANNEL_PARTNER = 'Partner';

    public static final String BLOCK_INTERNAL_ONLY =
        'Article is Internal App only and cannot be emailed to customers.';
    public static final String BLOCK_NOT_ATTACHED =
        'Article is not associated to the Case; attach it first for resolution metrics.';

    public class CaseArticleGuidanceResult {
        @AuraEnabled public Boolean canAttachToCase;
        @AuraEnabled public Boolean canEmailToCustomer;
        @AuraEnabled public String attachSteps;
        @AuraEnabled public String emailSteps;
        @AuraEnabled public String blockingReason;
        @AuraEnabled public String recommendedAction;
        @AuraEnabled public String metricsNote;
    }

    /**
     * L1 how-to guidance: how to attach a Knowledge article to a Case and email
     * its content from the console. Does not perform DML or send email.
     */
    public static CaseArticleGuidanceResult describeAttachAndEmailSteps(
        String articleChannel,
        Boolean alreadyAttachedToCase
    ) {
        CaseArticleGuidanceResult result = new CaseArticleGuidanceResult();
        result.canAttachToCase = true;
        result.metricsNote =
            'Attaching via ' + RELATED_LIST_CASE_ARTICLES
            + ' (CaseArticle) tracks the article in resolution / Knowledge usage metrics.';
        result.attachSteps =
            'Open the active Case in Service Console. Use the '
            + COMPONENT_KNOWLEDGE + ' / ' + COMPONENT_ARTICLES
            + ' component or the ' + RELATED_LIST_CASE_ARTICLES
            + ' related list to associate the Knowledge article to the Case.';
        result.emailSteps =
            'Open ' + CONSOLE_EMAIL_COMPOSER
            + ' on the Case. Use ' + ACTION_INSERT_KNOWLEDGE + ' or '
            + ACTION_SHARE_ARTICLE
            + ' (or paste the customer-visible article body) so the text is included '
            + 'in the outbound email, then send.';

        Boolean isCustomerVisible =
            articleChannel == CHANNEL_CUSTOMER || articleChannel == CHANNEL_PARTNER;

        if (articleChannel == CHANNEL_INTERNAL || !isCustomerVisible) {
            result.canEmailToCustomer = false;
            result.blockingReason = BLOCK_INTERNAL_ONLY;
            result.recommendedAction =
                'Publish or share the article to a customer-visible channel before '
                + 'inserting it into the customer email. You can still attach it to '
                + 'the Case for internal resolution metrics.';
            return result;
        }

        result.canEmailToCustomer = true;

        if (alreadyAttachedToCase != true) {
            result.blockingReason = BLOCK_NOT_ATTACHED;
            result.recommendedAction =
                'Attach the article to the Case first (' + RELATED_LIST_CASE_ARTICLES
                + '), then insert article content into the console email.';
            return result;
        }

        result.blockingReason = null;
        result.recommendedAction =
            'Article is attached and customer-visible. Insert content via '
            + CONSOLE_EMAIL_COMPOSER + ' and send.';
        return result;
    }

    /**
     * L2 diagnosis: why Insert Knowledge / email article content is unavailable.
     */
    public static CaseArticleGuidanceResult diagnoseEmailUnavailable(
        String articleChannel,
        Boolean alreadyAttachedToCase
    ) {
        CaseArticleGuidanceResult result = describeAttachAndEmailSteps(
            articleChannel,
            alreadyAttachedToCase
        );

        if (articleChannel == CHANNEL_INTERNAL) {
            result.blockingReason = BLOCK_INTERNAL_ONLY;
            result.recommendedAction =
                'Internal-only Knowledge articles are excluded from customer email insert. '
                + 'Change channel visibility or use a customer-published version.';
            result.canEmailToCustomer = false;
            return result;
        }

        if (alreadyAttachedToCase != true) {
            result.blockingReason = BLOCK_NOT_ATTACHED;
            result.recommendedAction =
                'Associate the article to the Case via ' + RELATED_LIST_CASE_ARTICLES
                + ' so metrics track usage, then retry Insert Knowledge in Email.';
            return result;
        }

        result.recommendedAction =
            'Confirm the agent has Email and Knowledge console permissions, and that '
            + 'the article is published to ' + CHANNEL_CUSTOMER + '.';
        return result;
    }

    /**
     * Returns true when the inbound request is instructional (L1 how-to) rather
     * than an imperative mutation ("attach/send it now").
     */
    public static Boolean isHowToGuidanceRequest(String issueText) {
        if (String.isBlank(issueText)) {
            return false;
        }
        String lower = issueText.toLowerCase();
        return lower.contains('how do i')
            || lower.contains('how to')
            || lower.contains('how can i');
    }
}
