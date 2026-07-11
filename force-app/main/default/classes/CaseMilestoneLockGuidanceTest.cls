@IsTest
private class CaseMilestoneLockGuidanceTest {
    @IsTest
    static void diagnose_recognizesMilestoneLockAndBlocksOverride() {
        CaseMilestoneLockGuidance.MilestoneLockDiagnosis result =
            CaseMilestoneLockGuidance.diagnoseStatusChangeBlocked(
                CaseMilestoneLockGuidance.ERROR_MILESTONE_LOCKED,
                CaseMilestoneLockGuidance.TARGET_STATUS_WAITING_ON_CUSTOMER
            );

        System.assertEquals(true, result.isMilestoneLockError);
        System.assertEquals(false, result.overrideAllowed);
        System.assertEquals(
            CaseMilestoneLockGuidance.BLOCK_NO_OVERRIDE,
            result.blockingReason
        );
        System.assert(
            result.recommendedAction.contains('Wait for the open system transaction'),
            result.recommendedAction
        );
        System.assert(
            result.recoverySteps.contains('Salesforce admin'),
            result.recoverySteps
        );
        System.assertEquals(
            CaseMilestoneLockGuidance.TARGET_STATUS_WAITING_ON_CUSTOMER,
            result.targetStatus
        );
    }

    @IsTest
    static void diagnose_nonMatchingError_asksForEscalationContext() {
        CaseMilestoneLockGuidance.MilestoneLockDiagnosis result =
            CaseMilestoneLockGuidance.diagnoseStatusChangeBlocked(
                'FIELD_CUSTOM_VALIDATION_EXCEPTION: Status cannot be Closed',
                'Closed'
            );

        System.assertEquals(false, result.isMilestoneLockError);
        System.assertEquals(false, result.overrideAllowed);
        System.assert(
            result.blockingReason.contains('does not match'),
            result.blockingReason
        );
        System.assertEquals('Closed', result.targetStatus);
    }

    @IsTest
    static void matchesMilestoneLockIssue_detectsSupportQuestion() {
        String issue =
            'I am trying to resolve a case before the 1-hour critical response '
            + 'milestone expires. I added a case comment and changed the status '
            + 'to Waiting on Customer. When I hit save, I get an error: '
            + CaseMilestoneLockGuidance.ERROR_MILESTONE_LOCKED
            + ' How do I override this?';

        System.assertEquals(
            true,
            CaseMilestoneLockGuidance.matchesMilestoneLockIssue(issue)
        );
        System.assertEquals(
            false,
            CaseMilestoneLockGuidance.matchesMilestoneLockIssue(
                'Why is Publish greyed out on my Spanish draft?'
            )
        );
    }
}
