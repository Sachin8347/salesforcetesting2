/**
 * REST entry for Jataka auto-resolution to post a visible Case resolution
 * (Feed + Status/Subject) so agents/CEOs can see the change in Service Console.
 *
 * Does not require Lightning Knowledge. Safe for L1 how-to demos.
 */
@RestResource(urlMapping='/jataka/v1/case-resolution')
global with sharing class KnowledgeCaseResolutionRest {
    global class ActionRequest {
        public String caseId;
        public String resolutionBody;
        public String newStatus;
        public String subjectPrefix;
    }

    global class ActionResponse {
        public Boolean success;
        public String caseId;
        public String caseNumber;
        public String status;
        public String subject;
        public String feedItemId;
        public String message;
    }

    @HttpPost
    global static ActionResponse postAction() {
        ActionRequest body = (ActionRequest) JSON.deserialize(
            RestContext.request.requestBody.toString(),
            ActionRequest.class
        );

        if (String.isBlank(body.caseId)) {
            throw new IllegalArgumentException('caseId is required.');
        }

        Case c = [
            SELECT Id, CaseNumber, Status, Subject
            FROM Case
            WHERE Id = :body.caseId
            LIMIT 1
        ];

        String feedBody = String.isBlank(body.resolutionBody)
            ? KnowledgeCaseResolutionService.describeAttachAndEmailSteps(
                  KnowledgeCaseResolutionService.CHANNEL_INTERNAL,
                  false
              ).attachSteps
              + '\n\n'
              + KnowledgeCaseResolutionService.describeAttachAndEmailSteps(
                    KnowledgeCaseResolutionService.CHANNEL_INTERNAL,
                    false
                ).emailSteps
            : body.resolutionBody;

        FeedItem post = new FeedItem();
        post.ParentId = c.Id;
        post.Type = 'TextPost';
        post.Body = feedBody.length() > 10000 ? feedBody.substring(0, 10000) : feedBody;
        insert post;

        String prefix = String.isBlank(body.subjectPrefix)
            ? '[Jataka] '
            : body.subjectPrefix;
        if (c.Subject == null || !c.Subject.startsWith(prefix)) {
            c.Subject = prefix + (c.Subject == null ? c.CaseNumber : c.Subject);
        }

        if (!String.isBlank(body.newStatus)) {
            c.Status = body.newStatus;
        } else if (c.Status == 'New') {
            c.Status = 'Working';
        }
        update c;

        c = [
            SELECT Id, CaseNumber, Status, Subject
            FROM Case
            WHERE Id = :c.Id
            LIMIT 1
        ];

        ActionResponse response = new ActionResponse();
        response.success = true;
        response.caseId = c.Id;
        response.caseNumber = c.CaseNumber;
        response.status = c.Status;
        response.subject = c.Subject;
        response.feedItemId = post.Id;
        response.message =
            'Case ' + c.CaseNumber + ' updated to ' + c.Status
            + ' with Jataka resolution Feed post.';
        return response;
    }
}
