public with sharing class QuickAccountController {
    @AuraEnabled
    public static Account createAccount(
        String name, 
        String accNumber, 
        String phone, 
        String website, 
        String industry, 
        Decimal revenue, 
        Integer employees, 
        String city
    ) {
        try {
            Account newAcc = new Account(
                Name = name,
                AccountNumber = accNumber,
                Phone = phone,
                Website = website,
                Industry = industry,
                AnnualRevenue = revenue,
                NumberOfEmployees = employees,
                BillingCity = city
            );
            
            // --- FIX FOR DUPLICATES ---
            // Create DML Options to override Duplicate Rules
            Database.DMLOptions dml = new Database.DMLOptions();
            dml.DuplicateRuleHeader.allowSave = true; // <--- This forces the save
            dml.DuplicateRuleHeader.runAsCurrentUser = true;
            
            // Use Database.insert instead of standard insert
            Database.SaveResult sr = Database.insert(newAcc, dml);
            
            if (sr.isSuccess()) {
                return newAcc;
            } else {
                // If it failed for another reason, throw exception
                throw new AuraHandledException('Error: ' + sr.getErrors()[0].getMessage());
            }
            // --------------------------

        } catch (Exception e) {
            throw new AuraHandledException('Error creating account: ' + e.getMessage());
        }
    }
}