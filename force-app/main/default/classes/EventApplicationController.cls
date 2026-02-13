public with sharing class EventApplicationController {
    
    @AuraEnabled
    public static Account createEventApplication(String applicationData) {
        try {
            // Parse the JSON application data
            Map<String, Object> appMap = (Map<String, Object>)JSON.deserializeUntyped(applicationData);
            
            // Create Account record to represent the Event Application
            Account newApplication = new Account();
            newApplication.Name = (String)appMap.get('firstName') + ' ' + (String)appMap.get('lastName') + ' - Event Application';
            newApplication.Type = 'Event Application';
            
            // Build description with all application details
            String description = 'Event Details:\n';
            description += 'Event Name: ' + (String)appMap.get('eventName') + '\n';
            description += 'Event Type: ' + (String)appMap.get('eventType') + '\n';
            description += 'Event Date: ' + (String)appMap.get('eventDate') + '\n';
            description += 'Expected Attendees: ' + String.valueOf(appMap.get('expectedAttendees')) + '\n';
            description += 'Event Description: ' + (String)appMap.get('eventDescription') + '\n\n';
            
            description += 'Applicant Information:\n';
            description += 'First Name: ' + (String)appMap.get('firstName') + '\n';
            description += 'Last Name: ' + (String)appMap.get('lastName') + '\n';
            description += 'Email: ' + (String)appMap.get('email') + '\n';
            description += 'Phone: ' + (String)appMap.get('phone') + '\n';
            description += 'Company/Organization: ' + (String)appMap.get('company') + '\n\n';
            
            // Add requirements if any
            List<Object> requirements = (List<Object>)appMap.get('requirements');
            if (requirements != null && !requirements.isEmpty()) {
                description += 'Requirements:\n';
                for (Object reqObj : requirements) {
                    String requirement = (String)reqObj;
                    description += '- ' + requirement.replace('_', ' ').toUpperCase() + '\n';
                }
                description += '\n';
            }
            
            // Add additional requirements if provided
            String additionalReqs = (String)appMap.get('additionalRequirements');
            if (String.isNotBlank(additionalReqs)) {
                description += 'Additional Requirements:\n' + additionalReqs;
            }
            
            newApplication.Description = description;
            
            // Set phone if provided
            String phone = (String)appMap.get('phone');
            if (String.isNotBlank(phone)) {
                newApplication.Phone = phone;
            }
            
            // Insert the application
            insert newApplication;
            
            return newApplication;
            
        } catch (Exception e) {
            throw new AuraHandledException('Error creating Event Application: ' + e.getMessage());
        }
    }
}
