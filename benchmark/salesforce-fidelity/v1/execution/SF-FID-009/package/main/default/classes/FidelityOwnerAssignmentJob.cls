public with sharing class FidelityOwnerAssignmentJob implements Queueable {
    private Id accountId;
    private Id ownerId;

    public FidelityOwnerAssignmentJob(Account accountRecord) {
        accountId = accountRecord.Id;
        ownerId = accountRecord.OwnerId;
    }

    public void execute(QueueableContext context) {
        update new Account(Id = accountId, OwnerId = ownerId);
    }
}
