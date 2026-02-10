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
        String city,
        String state,
        String postalCode,
        String type,
        String description,
        String ticker,
        String ownership,
        String sicCode,
        Integer yearStarted
    ) {
        try {
            // --- NEW BUSINESS LOGIC ---
            // Requirement: Enterprise accounts must have > $10M Revenue
            
            // -------------------------jgfvrffjhvvfjg-

            Account newAcc = new Account(
                Name = name,
                AccountNumber = accNumber,
                Phone = phone,
                Website = website,
                Industry = industry,
                AnnualRevenue = revenue,
                NumberOfEmployees = employees,
                BillingCity = city,
                BillingState = state,
                BillingPostalCode = postalCode,
                Type = type,
                Description = description,
                TickerSymbol = ticker,
                Ownership = ownership,
                SicCode = sicCode,
                YearStarted = yearStarted
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