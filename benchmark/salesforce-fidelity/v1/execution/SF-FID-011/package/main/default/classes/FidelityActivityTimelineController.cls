public with sharing class FidelityActivityTimelineController {
    @AuraEnabled(cacheable=true)
    public static List<Task> loadTimeline(Id accountId) {
        return [
            SELECT Id, Subject, Description, ActivityDate, WhoId, WhatId, CreatedDate
            FROM Task WHERE WhatId = :accountId ORDER BY CreatedDate DESC
        ];
    }
}
