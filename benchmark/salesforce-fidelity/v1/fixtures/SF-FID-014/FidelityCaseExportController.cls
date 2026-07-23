public without sharing class FidelityCaseExportController {
    @AuraEnabled
    public static List<Case> exportOpenCases() {
        return [SELECT Id, CaseNumber, Subject, ContactEmail FROM Case WHERE IsClosed = false];
    }
}
