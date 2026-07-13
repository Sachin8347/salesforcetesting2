@IsTest
private class JatakaDemoFixtureServiceTest {
    @IsTest
    static void seed_all_createsTranslationCaseAndAccount() {
        Test.startTest();
        JatakaDemoFixtureService.SeedResult first = JatakaDemoFixtureService.seed('all');
        JatakaDemoFixtureService.SeedResult second = JatakaDemoFixtureService.seed('all');
        Test.stopTest();

        System.assertEquals(true, first.success, first.message);
        System.assertEquals(8, first.records.size());
        System.assertEquals(true, second.success, second.message);
        System.assertEquals(8, second.records.size());

        Integer createdOnSecondPass = 0;
        for (JatakaDemoFixtureService.FixtureRecord row : second.records) {
            if (row.created) {
                createdOnSecondPass++;
            }
        }
        System.assertEquals(
            0,
            createdOnSecondPass,
            'Second seed pass should refresh existing demo records, not create duplicates.'
        );

        List<Knowledge_Translation_Request__c> drafts = [
            SELECT Id, Name, Translation_Status__c
            FROM Knowledge_Translation_Request__c
            WHERE Name = :JatakaDemoFixtureService.TRANSLATION_NAME
        ];
        System.assertEquals(1, drafts.size());
        System.assertEquals(
            KnowledgeTranslationPublishService.STATUS_DRAFT,
            drafts[0].Translation_Status__c
        );

        List<Case> cases = [
            SELECT Id, Subject
            FROM Case
            WHERE Subject LIKE 'JATAKA_DEMO_%'
        ];
        System.assertEquals(6, cases.size());

        List<Account> accounts = [
            SELECT Id
            FROM Account
            WHERE Name = :JatakaDemoFixtureService.ACCOUNT_NAME
        ];
        Boolean accountSeeded = false;
        for (JatakaDemoFixtureService.FixtureRecord row : first.records) {
            if (row.objectApiName == 'Account' && row.recordId != null) {
                accountSeeded = true;
            }
        }
        if (accountSeeded) {
            System.assertEquals(1, accounts.size());
        } else {
            System.assertEquals(
                0,
                accounts.size(),
                'When org Account automation blocks seeding, no Account row is expected.'
            );
        }
    }

    @IsTest
    static void status_returnsExistingFixtures() {
        JatakaDemoFixtureService.seed('knowledge-publish-blocked');
        JatakaDemoFixtureService.SeedResult status =
            JatakaDemoFixtureService.status('knowledge-publish-blocked');
        System.assertEquals(true, status.success);
        System.assertEquals(1, status.records.size());
        System.assertEquals(
            'Knowledge_Translation_Request__c',
            status.records[0].objectApiName
        );
    }

    @IsTest
    static void rest_seedAndStatus() {
        RestRequest req = new RestRequest();
        req.requestBody = Blob.valueOf(
            JSON.serialize(
                new Map<String, Object>{
                    'action' => 'seed',
                    'scenarioId' => 'attach-article-to-case'
                }
            )
        );
        RestContext.request = req;
        RestContext.response = new RestResponse();

        JatakaDemoFixtureRest.SeedResultDto seeded = JatakaDemoFixtureRest.postAction();
        System.assertEquals(true, seeded.success);
        System.assertEquals(1, seeded.records.size());
        System.assertEquals('Case', seeded.records[0].objectApiName);

        RestRequest getReq = new RestRequest();
        getReq.params.put('scenarioId', 'attach-article-to-case');
        RestContext.request = getReq;
        JatakaDemoFixtureRest.SeedResultDto status = JatakaDemoFixtureRest.getStatus();
        System.assertEquals(true, status.success);
        System.assertEquals(1, status.records.size());
    }

    @IsTest
    static void controller_seedDemoFixtures() {
        JatakaDemoFixtureService.SeedResult result =
            JatakaDemoFixtureController.seedDemoFixtures('attach-article-to-case');
        System.assertEquals(true, result.success);
        System.assertEquals(1, result.records.size());
        System.assertEquals('Case', result.records[0].objectApiName);
    }

    @IsTest
    static void seed_parentChildAndEntitlementAndClone() {
        JatakaDemoFixtureService.SeedResult entitlement =
            JatakaDemoFixtureService.seed('missing-entitlement-timer');
        System.assertEquals(true, entitlement.success);
        System.assertEquals(1, entitlement.records.size());
        System.assertEquals('Case', entitlement.records[0].objectApiName);

        JatakaDemoFixtureService.SeedResult parentChild =
            JatakaDemoFixtureService.seed('parent-child-cases');
        System.assertEquals(true, parentChild.success);
        System.assertEquals(2, parentChild.records.size());

        Case child = [
            SELECT Id, ParentId, Subject
            FROM Case
            WHERE Subject = :JatakaDemoFixtureService.CASE_SUBJECT_CHILD
            LIMIT 1
        ];
        Case parentCase = [
            SELECT Id
            FROM Case
            WHERE Subject = :JatakaDemoFixtureService.CASE_SUBJECT_PARENT
            LIMIT 1
        ];
        System.assertEquals(parentCase.Id, child.ParentId);

        JatakaDemoFixtureService.SeedResult cloneCase =
            JatakaDemoFixtureService.seed('case-clone-assignment');
        System.assertEquals(true, cloneCase.success);
        System.assertEquals(1, cloneCase.records.size());
    }

    @IsTest
    static void seed_salesAccount_isResilient() {
        JatakaDemoFixtureService.SeedResult result =
            JatakaDemoFixtureService.seed('sales-lead-assignment');
        System.assertEquals(true, result.success);
        System.assertEquals(1, result.records.size());
        System.assertEquals('Account', result.records[0].objectApiName);
        System.assert(
            result.records[0].recordId != null ||
                result.records[0].status == 'SEED_SKIPPED',
            'Account should either seed or soft-skip on org automation conflicts.'
        );
    }
}
