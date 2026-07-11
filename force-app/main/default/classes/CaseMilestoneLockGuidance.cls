/**
 * Encodes supported troubleshooting for Case status updates blocked by an
 * Entitlement Milestone lock (MCP L2 consumer-support fixture).
 *
 * Platform ground truth:
 * - When an Entitlement Milestone is mid-transaction (completion, violation,
 *   or SLA recalculation), Salesforce locks related Case status changes.
 * - Typical error: "Cannot modify case status because the underlying
 *   Entitlement Milestone is locked by an open system transaction."
 * - There is NO supported end-user override that bypasses the platform lock.
 *
 * Supported recovery (answer-only — no automated entitlement mutation):
 * 1. Wait for the open system transaction to finish, then retry the Case
 *    Status change (e.g. Waiting on Customer) and Case Comment save.
 * 2. Confirm Entitlement / Case Milestone state in Service Console (open
 *    milestones, completion flags, violation timers).
 * 3. If the lock persists after retries, escalate to a Salesforce admin to
 *    repair stuck milestone/entitlement state — do not edit CaseMilestone
 *    rows directly from unsupported tooling.
 * 4. Never instruct agents to "override" or force-unlock the milestone.
 */
public with sharing class CaseMilestoneLockGuidance {
    public static final String ERROR_MILESTONE_LOCKED =
        'Cannot modify case status because the underlying Entitlement Milestone '
        + 'is locked by an open system transaction.';

    public static final String TARGET_STATUS_WAITING_ON_CUSTOMER =
        'Waiting on Customer';

    public static final String BLOCK_NO_OVERRIDE =
        'There is no supported override that bypasses an Entitlement Milestone '
        + 'lock held by an open system transaction.';

    public static final String ACTION_WAIT_AND_RETRY =
        'Wait for the open system transaction to complete, then retry saving '
        + 'the Case Comment and Status change.';

    public static final String ACTION_VERIFY_MILESTONE =
        'Verify Entitlement and Case Milestone state (open milestones, '
        + 'completion, violation timers) in Service Console.';

    public static final String ACTION_ADMIN_REPAIR =
        'If the lock persists after retries, escalate to a Salesforce admin '
        + 'to repair stuck milestone/entitlement state. Do not edit '
        + 'CaseMilestone records directly via unsupported tooling.';

    public class MilestoneLockDiagnosis {
        @AuraEnabled public Boolean isMilestoneLockError;
        @AuraEnabled public Boolean overrideAllowed;
        @AuraEnabled public String blockingReason;
        @AuraEnabled public String recommendedAction;
        @AuraEnabled public String recoverySteps;
        @AuraEnabled public String targetStatus;
    }

    /**
     * L2 diagnosis: why Case Status cannot change while a milestone is locked,
     * and what supported recovery looks like. Does not perform DML.
     */
    public static MilestoneLockDiagnosis diagnoseStatusChangeBlocked(
        String errorMessage,
        String attemptedStatus
    ) {
        MilestoneLockDiagnosis result = new MilestoneLockDiagnosis();
        result.overrideAllowed = false;
        result.targetStatus = String.isBlank(attemptedStatus)
            ? TARGET_STATUS_WAITING_ON_CUSTOMER
            : attemptedStatus;

        String normalized = String.isBlank(errorMessage)
            ? ''
            : errorMessage.toLowerCase();

        Boolean matchesLock =
            normalized.contains('entitlement milestone is locked')
            || normalized.contains('milestone is locked by an open system transaction')
            || normalized.contains(ERROR_MILESTONE_LOCKED.toLowerCase());

        result.isMilestoneLockError = matchesLock;

        if (!matchesLock) {
            result.blockingReason =
                'Error does not match the Entitlement Milestone lock signature.';
            result.recommendedAction =
                'Capture the full validation message and Case Id, then escalate '
                + 'with Entitlement Process / Milestone configuration context.';
            result.recoverySteps =
                'Confirm whether Entitlements are enabled, whether a milestone '
                + 'is completing concurrently, and whether another automation '
                + 'is updating the Case in the same transaction.';
            return result;
        }

        result.blockingReason = BLOCK_NO_OVERRIDE;
        result.recommendedAction =
            ACTION_WAIT_AND_RETRY + ' ' + ACTION_VERIFY_MILESTONE;
        result.recoverySteps =
            '1) ' + ACTION_WAIT_AND_RETRY
            + ' 2) ' + ACTION_VERIFY_MILESTONE
            + ' 3) ' + ACTION_ADMIN_REPAIR
            + ' Attempted status: ' + result.targetStatus + '.';
        return result;
    }

    /**
     * True when the inbound text describes the milestone-lock Case Status failure.
     */
    public static Boolean matchesMilestoneLockIssue(String issueText) {
        if (String.isBlank(issueText)) {
            return false;
        }
        String lower = issueText.toLowerCase();
        return lower.contains('entitlement milestone')
            && (lower.contains('locked') || lower.contains('open system transaction'));
    }
}

