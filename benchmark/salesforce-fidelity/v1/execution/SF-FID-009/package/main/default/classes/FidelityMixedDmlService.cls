public with sharing class FidelityMixedDmlService {
    public static void activateOwner(User owner, Account accountRecord) {
        owner.IsActive = true;
        update owner;
        accountRecord.OwnerId = owner.Id;
        update accountRecord;
    }
}
