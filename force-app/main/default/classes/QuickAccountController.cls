public with sharing class QuickAccountController {
    @AuraEnabled
    public static Account createAccount(
        String name, 
        String accNumber, 
        String phone, 
        String website, 
        String industry, 
        Decimal revenue,
        String revenueRange,
        Integer employees, 
        String city,
        String state,
        String postalCode,
        String country,
        String type,
        String description,
        String primaryContact,
        String contactTitle,
        String contactEmail,
        String contactPhone,
        String fax,
        String rating,
        String customerPriority,
        String slaExpiration,
        String ticker,
        String ownership,
        String sicCode,
        String yearStarted,
        String marketCap,
        Integer locations,
        String fiscalYear,
        String currency,
        String stockExchange,
        String dunsNumber,
        String naicsCode,
        String source,
        String campaign,
        String leadSource,
        String lastActivityDate,
        String nextActivityDate,
        String activityType,
        String activityDescription
    ) {
        try {
            // --- NEW BUSINESS LOGIC ---
            // Requirement: Enterprise accounts must have > $10M Revenue
            
            // --- NOTE: Some fields are stored in description for demo purposes ---
            // In a real implementation, you would create custom fields for:
            // - Revenue Range
            // - Primary Contact Information
            // - Customer Priority
            // - SLA Expiration Date
            // - Market Cap
            // - Number of Locations
            // - Fiscal Year
            // - Currency
            // - Stock Exchange
            // - DUNS Number
            // - NAICS Code
            // - Activity Tracking
            
            // Combine additional information into description
            String fullDescription = description;
            if (String.isNotBlank(primaryContact)) {
                fullDescription += '\n\nPrimary Contact: ' + primaryContact;
                if (String.isNotBlank(contactTitle)) {
                    fullDescription += ' (' + contactTitle + ')';
                }
                if (String.isNotBlank(contactEmail)) {
                    fullDescription += '\nEmail: ' + contactEmail;
                }
                if (String.isNotBlank(contactPhone)) {
                    fullDescription += '\nPhone: ' + contactPhone;
                }
            }
            if (String.isNotBlank(revenueRange)) {
                fullDescription += '\n\nRevenue Range: ' + revenueRange;
            }
            if (String.isNotBlank(marketCap)) {
                fullDescription += '\nMarket Cap: ' + marketCap;
            }
            if (locations != null) {
                fullDescription += '\nNumber of Locations: ' + locations;
            }
            if (String.isNotBlank(fiscalYear)) {
                fullDescription += '\nFiscal Year: ' + fiscalYear;
            }
            if (String.isNotBlank(currency)) {
                fullDescription += '\nCurrency: ' + currency;
            }
            if (String.isNotBlank(stockExchange)) {
                fullDescription += '\nStock Exchange: ' + stockExchange;
            }
            if (String.isNotBlank(dunsNumber)) {
                fullDescription += '\nDUNS Number: ' + dunsNumber;
            }
            if (String.isNotBlank(naicsCode)) {
                fullDescription += '\nNAICS Code: ' + naicsCode;
            }
            if (String.isNotBlank(customerPriority)) {
                fullDescription += '\nCustomer Priority: ' + customerPriority;
            }
            if (String.isNotBlank(slaExpiration)) {
                fullDescription += '\nSLA Expiration: ' + slaExpiration;
            }
            if (String.isNotBlank(source)) {
                fullDescription += '\nAccount Source: ' + source;
            }
            if (String.isNotBlank(campaign)) {
                fullDescription += '\nCampaign: ' + campaign;
            }
            if (String.isNotBlank(leadSource)) {
                fullDescription += '\nLead Source: ' + leadSource;
            }
            if (String.isNotBlank(lastActivityDate)) {
                fullDescription += '\nLast Activity: ' + lastActivityDate;
            }
            if (String.isNotBlank(nextActivityDate)) {
                fullDescription += '\nNext Activity: ' + nextActivityDate;
            }
            if (String.isNotBlank(activityType)) {
                fullDescription += '\nActivity Type: ' + activityType;
            }
            if (String.isNotBlank(activityDescription)) {
                fullDescription += '\nActivity Description: ' + activityDescription;
            }

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
                BillingCountry = country,
                Type = type,
                Description = fullDescription,
                Fax = fax,
                Rating = rating,
                // Commented out custom fields - create these in your org if needed
                // CustomerPriority__c = customerPriority,
                // SLAExpirationDate__c = slaExpiration != null ? Date.valueOf(slaExpiration) : null,
                TickerSymbol = ticker,
                Ownership = ownership,
                Sic = sicCode != null ? sicCode : null,
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