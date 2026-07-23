@IsTest
private class FidelityBenchmark007Test {
    @IsTest
    static void verifiesSensitiveFieldReadIsRemoved() {
        List<FieldPermissions> permissions = [
            SELECT Field, PermissionsRead, Parent.Name
            FROM FieldPermissions
            WHERE Field = 'Contact.SSN__c' AND Parent.Name = 'Guest Checkout'
        ];
        System.assertEquals(1, permissions.size());
        System.assertEquals(false, permissions[0].PermissionsRead);
    }
}
