global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        return new Map<String, Object>();
    }

    global static Map<String, Object> run() {
        List<FieldPermissions> permissions = [
            SELECT Field, PermissionsRead, Parent.Name
            FROM FieldPermissions
            WHERE Field = 'Contact.SSN__c' AND Parent.Name = 'Guest Checkout'
        ];
        return new Map<String, Object>{
            'rowCount' => permissions.size(),
            'permissionsRead' =>
                permissions.isEmpty() ? null : permissions[0].PermissionsRead
        };
    }
}
