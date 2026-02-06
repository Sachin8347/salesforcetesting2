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
            // --- NEW BUSINESS LOGIC ---
            // Requirement: Enterprise accounts must have > $10M Revenue
            // if (revenue != null && revenue < 10000000) {
            //    throw new AuraHandledException('Business Rule Violation: Enterprise Accounts must have Annual Revenue of at least $10,000,000.');
            // }
            // --------------------------

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
            
            // Allow duplicates for demo purposes
            Database.DMLOptions dml = new Database.DMLOptions();
            dml.DuplicateRuleHeader.allowSave = true; 
            dml.DuplicateRuleHeader.runAsCurrentUser = true;
            
            Database.SaveResult sr = Database.insert(newAcc, dml);
            
            if (sr.isSuccess()) {
                return newAcc;
            } else {
                throw new AuraHandledException('Error: ' + sr.getErrors()[0].getMessage());
            }

        } catch (Exception e) {
            // Pass the error back to the LWC
            throw new AuraHandledException(e.getMessage());
        }
    }
}