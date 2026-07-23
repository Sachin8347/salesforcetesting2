global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        Account parent = new Account(Name = 'Fidelity UI Timeline');
        insert parent;
        List<Task> records = new List<Task>();
        for (Integer i = 0; i < 201; i++) {
            records.add(new Task(
                WhatId = parent.Id,
                Subject = 'Fidelity UI Activity ' + i,
                Status = 'Not Started',
                Priority = 'Normal'
            ));
        }
        insert records;
        return new Map<String, Object>{'accountId' => parent.Id};
    }

    global static Map<String, Object> run() {
        Id accountId = [
            SELECT Id FROM Account WHERE Name = 'Fidelity UI Timeline' LIMIT 1
        ].Id;
        List<Task> result =
            FidelityActivityTimelineController.loadTimeline(accountId);
        return new Map<String, Object>{'timelineCount' => result.size()};
    }
}
