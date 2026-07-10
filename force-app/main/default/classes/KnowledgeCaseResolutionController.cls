/**
 * L1 entry point for Knowledge + Case article attach/email troubleshooting in MCP tests.
 */
public with sharing class KnowledgeCaseResolutionController {
    @AuraEnabled(cacheable=true)
    public static KnowledgeCaseResolutionService.CaseArticleGuidanceResult getAttachAndEmailGuidance(
        String articleChannel,
        Boolean alreadyAttachedToCase
    ) {
        return KnowledgeCaseResolutionService.describeAttachAndEmailSteps(
            articleChannel,
            alreadyAttachedToCase == true
        );
    }

    @AuraEnabled(cacheable=true)
    public static KnowledgeCaseResolutionService.CaseArticleGuidanceResult diagnoseEmailBlock(
        String articleChannel,
        Boolean alreadyAttachedToCase
    ) {
        return KnowledgeCaseResolutionService.diagnoseEmailUnavailable(
            articleChannel,
            alreadyAttachedToCase == true
        );
    }
}
