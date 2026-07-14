/**
 * Idempotent CEO-demo fixture seeder for salesforcetesting2.
 *
 * Creates/refreshes records with a stable JATAKA_DEMO_ prefix so the
 * dashboard can provision org situations without mutating production data.
 *
 * Compatibility note (impact analysis):
 * - Consumes KnowledgeTranslationPublishService public constants only.
 * - Inserts Knowledge_Translation_Request__c using the same field pattern as
 *   KTAutoResolutionRestTest — does not change existing publish/REST behavior.
 * - Seeds Case Description text that matches CaseMilestoneLockGuidance signatures
 *   without editing CaseMilestoneLockGuidance or CaseMilestone rows.
 */
public with sharing class JatakaDemoFixtureService {
    public static final String PREFIX = 'JATAKA_DEMO_';
    public static final String TRANSLATION_NAME = 'JATAKA_DEMO_Spanish_Draft';
    public static final String CASE_SUBJECT_ATTACH = 'JATAKA_DEMO_Attach_Article_Case';
    public static final String CASE_SUBJECT_MILESTONE = 'JATAKA_DEMO_Milestone_Lock_Case';
    public static final String CASE_SUBJECT_ENTITLEMENT = 'JATAKA_DEMO_Missing_Entitlement_Case';
    public static final String CASE_SUBJECT_PARENT = 'JATAKA_DEMO_Parent_Implementation_Case';
    public static final String CASE_SUBJECT_CHILD = 'JATAKA_DEMO_Child_IT_Subtask_Case';
    public static final String CASE_SUBJECT_CLONE = 'JATAKA_DEMO_Clone_Assignment_Case';
    public static final String CASE_SUBJECT_PRICEBOOK = 'JATAKA_DEMO_Pricebook_Entry_Missing_Case';
    public static final String CASE_SUBJECT_ADD_PRODUCTS = 'JATAKA_DEMO_Add_Products_Button_Case';
    public static final String CASE_SUBJECT_QUOTE_PDF = 'JATAKA_DEMO_Quote_PDF_Logo_Case';
    public static final String ACCOUNT_NAME = 'JATAKA_DEMO_Sales_Account';

    public class FixtureRecord {
        @AuraEnabled public String objectApiName;
        @AuraEnabled public String recordId;
        @AuraEnabled public String externalKey;
        @AuraEnabled public String label;
        @AuraEnabled public String status;
        @AuraEnabled public String caseNumber;
        @AuraEnabled public Boolean created;
    }

    public class SeedResult {
        @AuraEnabled public Boolean success;
        @AuraEnabled public String message;
        @AuraEnabled public String scenarioId;
        @AuraEnabled public List<FixtureRecord> records;
    }

    /**
     * Seed all CEO demo scenarios (or one scenario when scenarioId is provided).
     * Supported scenario ids:
     * - knowledge-publish-blocked
     * - attach-article-to-case
     * - milestone-lock-guardrail
     * - sales-lead-assignment
     * - missing-entitlement-timer
     * - parent-child-cases
     * - case-clone-assignment
     * - pricebook-entry-missing
     * - opportunity-add-products-missing
     * - quote-pdf-logo-missing
     * - all (default)
     */
    private class CaseFixtureSpec {
        public String scenarioId;
        public String subject;
        public String description;
        public CaseFixtureSpec(String scenarioId, String subject, String description) {
            this.scenarioId = scenarioId;
            this.subject = subject;
            this.description = description;
        }
    }

    /**
     * Data-driven Case fixtures. Adding a new live Case scenario = one entry here
     * (plus matching CEO demo JSON). Special fixtures (translation / account /
     * parent-child) stay as dedicated helpers below.
     */
    private static List<CaseFixtureSpec> caseFixtureSpecs() {
        return new List<CaseFixtureSpec>{
            new CaseFixtureSpec(
                'attach-article-to-case',
                CASE_SUBJECT_ATTACH,
                'CEO demo Case for Knowledge article attach/email how-to.\n\n'
                    + 'I found an internal Knowledge Article that explains the resolution. '
                    + 'How do I attach this article directly to the active Case record layout '
                    + 'so it is tracked in our resolution metrics, and how can I send its text '
                    + 'content straight to the customer email via the console?'
            ),
            new CaseFixtureSpec(
                'milestone-lock-guardrail',
                CASE_SUBJECT_MILESTONE,
                'CEO demo Case for Entitlement Milestone lock diagnosis.\n\n'
                    + CaseMilestoneLockGuidance.ERROR_MILESTONE_LOCKED
                    + '\nI am trying to change Status to Waiting on Customer. How do I override this?'
            ),
            new CaseFixtureSpec(
                'missing-entitlement-timer',
                CASE_SUBJECT_ENTITLEMENT,
                'CEO demo Case for missing SLA Milestone timer.\n\n'
                    + 'I just opened a high-priority incident for an enterprise account. '
                    + 'They have an active service Contract, but the standard SLA Milestone '
                    + 'Countdown Timer widget is completely missing from the console sidebar. '
                    + 'How do I apply their contractual entitlement terms to this case record?'
            ),
            new CaseFixtureSpec(
                'case-clone-assignment',
                CASE_SUBJECT_CLONE,
                'CEO demo Case for Clone assignment-rule bypass.\n\n'
                    + 'When I take an old resolved case and click the standard Clone button '
                    + 'to open a new related ticket, the new case stays assigned to me instead '
                    + 'of automatically routing to the Tier 1 Queue. How do I make Clone honor '
                    + 'assignment rules?'
            ),
            new CaseFixtureSpec(
                'pricebook-entry-missing',
                CASE_SUBJECT_PRICEBOOK,
                'Lead conversion error: Missing pricebook entry on automatic line item mapping\n\n'
                    + 'I am trying to convert a qualified lead. Our system is configured to auto-create '
                    + 'an opportunity and map standard product lines from the lead custom fields. However, '
                    + 'when I click \'Convert\', I get an error: \'System.DmlException: Insert failed. '
                    + 'First exception on row 0; Standard Price Book has no price defined for product '
                    + 'B2B-Enterprise\'. I can\'t proceed with creating the opportunity. How do I fix this?'
            ),
            new CaseFixtureSpec(
                'opportunity-add-products-missing',
                CASE_SUBJECT_ADD_PRODUCTS,
                'Missing \'Add Products\' button on an Opportunity record layout\n\n'
                    + 'I need to build out a pipeline projection for a client, but when I navigate to the '
                    + 'Products related list on my newly created Opportunity, the \'Add Products\' and '
                    + '\'Choose Price Book\' buttons are entirely missing. My colleague can see them on '
                    + 'her opportunities. What steps do I need to follow to make them appear?'
            ),
            new CaseFixtureSpec(
                'quote-pdf-logo-missing',
                CASE_SUBJECT_QUOTE_PDF,
                'PDF Generation fails on Quote: Image asset broken or missing access rights\n\n'
                    + 'When I try to use the standard \'Create Quote PDF\' feature on my quote record, '
                    + 'the system generates a document but it completely leaves out our corporate logo, '
                    + 'displaying a broken image icon instead. The rest of the table looks fine. How do I '
                    + 'fix the template layout so our logo loads correctly for customers?'
            )
        };
    }

    public static SeedResult seed(String scenarioId) {
        String key = String.isBlank(scenarioId) ? 'all' : scenarioId.trim();
        SeedResult result = new SeedResult();
        result.success = true;
        result.scenarioId = key;
        result.records = new List<FixtureRecord>();

        if (key == 'all' || key == 'knowledge-publish-blocked') {
            result.records.add(upsertTranslationDraft());
        }
        if (key == 'all' || key == 'sales-lead-assignment') {
            try {
                result.records.add(upsertDemoAccount());
            } catch (Exception e) {
                FixtureRecord fr = new FixtureRecord();
                fr.objectApiName = 'Account';
                fr.externalKey = ACCOUNT_NAME;
                fr.label = ACCOUNT_NAME;
                fr.status = 'SEED_SKIPPED';
                fr.created = false;
                result.records.add(fr);
                result.message =
                    (result.message == null ? '' : result.message + ' ')
                    + 'Account seed skipped due to org automation: '
                    + e.getMessage();
            }
        }
        if (key == 'all' || key == 'parent-child-cases') {
            result.records.addAll(upsertParentChildCases());
        }

        for (CaseFixtureSpec spec : caseFixtureSpecs()) {
            if (key == 'all' || key == spec.scenarioId) {
                result.records.add(upsertDemoCase(spec.subject, spec.description));
            }
        }

        if (result.records.isEmpty()) {
            result.success = false;
            result.message = 'Unknown scenarioId: ' + key;
            return result;
        }

        result.message =
            'Seeded ' + result.records.size() + ' demo fixture record(s) for ' + key + '.';
        return result;
    }

    public static SeedResult status(String scenarioId) {
        String key = String.isBlank(scenarioId) ? 'all' : scenarioId.trim();
        SeedResult result = new SeedResult();
        result.success = true;
        result.scenarioId = key;
        result.records = new List<FixtureRecord>();

        if (key == 'all' || key == 'knowledge-publish-blocked') {
            FixtureRecord tr = findTranslationDraft();
            if (tr != null) {
                result.records.add(tr);
            }
        }
        if (key == 'all' || key == 'sales-lead-assignment') {
            FixtureRecord a = findDemoAccount();
            if (a != null) {
                result.records.add(a);
            }
        }
        if (key == 'all' || key == 'parent-child-cases') {
            FixtureRecord parentCase = findDemoCase(CASE_SUBJECT_PARENT);
            FixtureRecord childCase = findDemoCase(CASE_SUBJECT_CHILD);
            if (parentCase != null) {
                result.records.add(parentCase);
            }
            if (childCase != null) {
                result.records.add(childCase);
            }
        }

        for (CaseFixtureSpec spec : caseFixtureSpecs()) {
            if (key == 'all' || key == spec.scenarioId) {
                FixtureRecord c = findDemoCase(spec.subject);
                if (c != null) {
                    result.records.add(c);
                }
            }
        }

        result.message =
            result.records.isEmpty()
                ? 'No demo fixtures found for ' + key + '.'
                : 'Found ' + result.records.size() + ' demo fixture record(s).';
        return result;
    }

    private static FixtureRecord upsertTranslationDraft() {
        List<Knowledge_Translation_Request__c> existing = [
            SELECT Id, Name, Translation_Status__c, Language_Code__c, Assigned_Queue__c
            FROM Knowledge_Translation_Request__c
            WHERE Name = :TRANSLATION_NAME
            LIMIT 1
        ];

        Knowledge_Translation_Request__c row;
        Boolean created = false;
        if (existing.isEmpty()) {
            row = new Knowledge_Translation_Request__c(
                Name = TRANSLATION_NAME,
                Language_Code__c = KnowledgeTranslationPublishService.LANG_SPANISH,
                Translation_Status__c = KnowledgeTranslationPublishService.STATUS_DRAFT,
                Assigned_Queue__c = KnowledgeTranslationPublishService.QUEUE_SPANISH,
                Master_Article_Id__c = 'JTK_DEMO_MASTER01'
            );
            insert row;
            created = true;
        } else {
            row = existing[0];
            row.Language_Code__c = KnowledgeTranslationPublishService.LANG_SPANISH;
            row.Translation_Status__c = KnowledgeTranslationPublishService.STATUS_DRAFT;
            row.Assigned_Queue__c = KnowledgeTranslationPublishService.QUEUE_SPANISH;
            update row;
        }

        FixtureRecord fr = new FixtureRecord();
        fr.objectApiName = 'Knowledge_Translation_Request__c';
        fr.recordId = row.Id;
        fr.externalKey = TRANSLATION_NAME;
        fr.label = TRANSLATION_NAME;
        fr.status = row.Translation_Status__c;
        fr.created = created;
        return fr;
    }

    private static FixtureRecord findTranslationDraft() {
        List<Knowledge_Translation_Request__c> existing = [
            SELECT Id, Name, Translation_Status__c
            FROM Knowledge_Translation_Request__c
            WHERE Name = :TRANSLATION_NAME
            LIMIT 1
        ];
        if (existing.isEmpty()) {
            return null;
        }
        FixtureRecord fr = new FixtureRecord();
        fr.objectApiName = 'Knowledge_Translation_Request__c';
        fr.recordId = existing[0].Id;
        fr.externalKey = TRANSLATION_NAME;
        fr.label = existing[0].Name;
        fr.status = existing[0].Translation_Status__c;
        fr.created = false;
        return fr;
    }

    private static FixtureRecord upsertDemoCase(String subject, String description) {
        List<Case> existing = [
            SELECT Id, CaseNumber, Subject, Status, Description
            FROM Case
            WHERE Subject = :subject
            LIMIT 1
        ];

        Case c;
        Boolean created = false;
        if (existing.isEmpty()) {
            c = new Case(
                Subject = subject,
                Description = description,
                Status = 'New',
                Origin = 'Web'
            );
            insert c;
            created = true;
            c = [
                SELECT Id, CaseNumber, Subject, Status
                FROM Case
                WHERE Id = :c.Id
                LIMIT 1
            ];
        } else {
            c = existing[0];
            c.Description = description;
            if (c.Status == null) {
                c.Status = 'New';
            }
            update c;
            c = [
                SELECT Id, CaseNumber, Subject, Status
                FROM Case
                WHERE Id = :c.Id
                LIMIT 1
            ];
        }

        FixtureRecord fr = new FixtureRecord();
        fr.objectApiName = 'Case';
        fr.recordId = c.Id;
        fr.externalKey = subject;
        fr.label = c.Subject;
        fr.status = c.Status;
        fr.caseNumber = c.CaseNumber;
        fr.created = created;
        return fr;
    }

    private static FixtureRecord findDemoCase(String subject) {
        List<Case> existing = [
            SELECT Id, CaseNumber, Subject, Status
            FROM Case
            WHERE Subject = :subject
            LIMIT 1
        ];
        if (existing.isEmpty()) {
            return null;
        }
        FixtureRecord fr = new FixtureRecord();
        fr.objectApiName = 'Case';
        fr.recordId = existing[0].Id;
        fr.externalKey = subject;
        fr.label = existing[0].Subject;
        fr.status = existing[0].Status;
        fr.caseNumber = existing[0].CaseNumber;
        fr.created = false;
        return fr;
    }

    private static List<FixtureRecord> upsertParentChildCases() {
        List<FixtureRecord> rows = new List<FixtureRecord>();
        FixtureRecord parentRec = upsertDemoCase(
            CASE_SUBJECT_PARENT,
            'CEO demo Parent Case for Parent-Child structure.\n\n'
                + 'I have an incoming system implementation case that requires actions from '
                + 'IT, Finance, and Shipping. I want to keep this Case open as an umbrella '
                + 'record and create tracking sub-tasks under it. How do I set that up?'
        );
        rows.add(parentRec);

        List<Case> children = [
            SELECT Id, CaseNumber, Subject, Status, ParentId
            FROM Case
            WHERE Subject = :CASE_SUBJECT_CHILD
            LIMIT 1
        ];
        Case child;
        Boolean created = false;
        if (children.isEmpty()) {
            child = new Case(
                Subject = CASE_SUBJECT_CHILD,
                Description =
                    'CEO demo Child Case (IT sub-task) linked to parent '
                    + parentRec.caseNumber + '.',
                Status = 'New',
                Origin = 'Web',
                ParentId = parentRec.recordId
            );
            insert child;
            created = true;
        } else {
            child = children[0];
            child.ParentId = parentRec.recordId;
            child.Description =
                'CEO demo Child Case (IT sub-task) linked to parent '
                + parentRec.caseNumber + '.';
            update child;
        }
        child = [
            SELECT Id, CaseNumber, Subject, Status
            FROM Case
            WHERE Id = :child.Id
            LIMIT 1
        ];

        FixtureRecord childRec = new FixtureRecord();
        childRec.objectApiName = 'Case';
        childRec.recordId = child.Id;
        childRec.externalKey = CASE_SUBJECT_CHILD;
        childRec.label = child.Subject;
        childRec.status = child.Status;
        childRec.caseNumber = child.CaseNumber;
        childRec.created = created;
        rows.add(childRec);
        return rows;
    }

    private static FixtureRecord upsertDemoAccount() {
        List<Account> existing = [
            SELECT Id, Name, Phone, AccountStatus__c
            FROM Account
            WHERE Name = :ACCOUNT_NAME
            LIMIT 1
        ];

        Account a;
        Boolean created = false;
        if (existing.isEmpty()) {
            a = new Account(
                Name = ACCOUNT_NAME,
                Phone = '555-0100',
                BillingCountry = 'United States',
                AccountStatus__c = AccountStatusService.STATUS_PENDING
            );
            insert a;
            created = true;
        } else {
            a = existing[0];
            if (String.isBlank(a.AccountStatus__c)) {
                a.AccountStatus__c = AccountStatusService.STATUS_PENDING;
                update a;
            }
        }

        FixtureRecord fr = new FixtureRecord();
        fr.objectApiName = 'Account';
        fr.recordId = a.Id;
        fr.externalKey = ACCOUNT_NAME;
        fr.label = a.Name;
        fr.status = a.AccountStatus__c;
        fr.created = created;
        return fr;
    }

    private static FixtureRecord findDemoAccount() {
        List<Account> existing = [
            SELECT Id, Name, AccountStatus__c
            FROM Account
            WHERE Name = :ACCOUNT_NAME
            LIMIT 1
        ];
        if (existing.isEmpty()) {
            return null;
        }
        FixtureRecord fr = new FixtureRecord();
        fr.objectApiName = 'Account';
        fr.recordId = existing[0].Id;
        fr.externalKey = ACCOUNT_NAME;
        fr.label = existing[0].Name;
        fr.status = existing[0].AccountStatus__c;
        fr.created = false;
        return fr;
    }
}
