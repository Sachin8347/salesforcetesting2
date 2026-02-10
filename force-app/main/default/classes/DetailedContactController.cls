public with sharing class DetailedContactController {
    
    @AuraEnabled
    public static Contact createContact(ContactData contactData) {
        try {
            // Create new Contact object
            Contact newContact = new Contact();
            
            // Set basic information
            newContact.FirstName = contactData.firstName;
            newContact.LastName = contactData.lastName;
            newContact.Email = contactData.email;
            newContact.Phone = contactData.phone;
            
            // Set birth date if provided
            if (String.isNotBlank(contactData.birthDate)) {
                newContact.Birthdate = Date.parse(contactData.birthDate);
            }
            
            // Set professional information
            // Note: Company is not a standard Contact field, using Account relationship instead
            newContact.Title = contactData.title;
            newContact.Department = contactData.department;
            
            // Set address information
            if (String.isNotBlank(contactData.street) || 
                String.isNotBlank(contactData.city) || 
                String.isNotBlank(contactData.state) || 
                String.isNotBlank(contactData.postalCode) || 
                String.isNotBlank(contactData.country)) {
                
                newContact.MailingStreet = contactData.street;
                newContact.MailingCity = contactData.city;
                newContact.MailingState = contactData.state;
                newContact.MailingPostalCode = contactData.postalCode;
                newContact.MailingCountry = contactData.country;
            }
            
            // Set additional information
            newContact.LeadSource = contactData.leadSource;
            
            // Insert the contact
            insert newContact;
            
            // Handle notes if provided
            if (String.isNotBlank(contactData.notes)) {
                // Create a note attachment for the contact
                Note note = new Note();
                note.ParentId = newContact.Id;
                note.Body = contactData.notes;
                note.Title = 'Contact Notes';
                insert note;
            }
            
            // Handle newsletter subscription
            if (contactData.newsletter) {
                // You could integrate with your marketing automation here
                // For now, we'll just add a description
                newContact.Description = (String.isNotBlank(newContact.Description) ? newContact.Description + '\n' : '') + 
                                       'Subscribed to newsletter on ' + System.now().format();
                update newContact;
            }
            
            // Return the created contact with all fields
            return [SELECT Id, Name, FirstName, LastName, Email, Phone, Birthdate, 
                          Title, Department, LeadSource, CreatedDate 
                   FROM Contact 
                   WHERE Id = :newContact.Id];
            
        } catch (Exception e) {
            // Log the error
            System.debug('Error creating contact: ' + e.getMessage());
            // Throw AuraHandledException to return error to LWC
            throw new AuraHandledException('Error creating contact: ' + e.getMessage());
        }
    }
    
    // Inner class to hold contact data
    public class ContactData {
        @AuraEnabled public String firstName { get; set; }
        @AuraEnabled public String lastName { get; set; }
        @AuraEnabled public String email { get; set; }
        @AuraEnabled public String phone { get; set; }
        @AuraEnabled public String birthDate { get; set; }
        @AuraEnabled public String company { get; set; }
        @AuraEnabled public String title { get; set; }
        @AuraEnabled public String department { get; set; }
        @AuraEnabled public String street { get; set; }
        @AuraEnabled public String city { get; set; }
        @AuraEnabled public String state { get; set; }
        @AuraEnabled public String postalCode { get; set; }
        @AuraEnabled public String country { get; set; }
        @AuraEnabled public String notes { get; set; }
        @AuraEnabled public String leadSource { get; set; }
        @AuraEnabled public Boolean newsletter { get; set; }
    }
}
