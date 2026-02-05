public with sharing class QuickAccountController {
    @AuraEnabled
    public static Account createAccount(String name, String phone) {
        try {
            
            Account newAcc = new Account(Name = name, Phone = phone);
            insert newAcc;
            return newAcc;
        } catch (Exception e) {
            throw new AuraHandledException('Error creating account: ' + e.getMessage());
        }
    }
    //khbhbjh
}