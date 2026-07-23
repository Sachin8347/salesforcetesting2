@IsTest
private class FidelityBenchmark011Test {
    @TestSetup
    static void seed() {
        Account accountRecord = new Account(Name = 'Fidelity Timeline');
        insert accountRecord;
        List<Task> tasks = new List<Task>();
        for (Integer i = 0; i < 201; i++) {
            tasks.add(new Task(
                WhatId = accountRecord.Id,
                Subject = 'Fidelity Activity ' + i,
                Status = 'Not Started',
                Priority = 'Normal'
            ));
        }
        insert tasks;
    }

    @IsTest
    static void verifiesTimelineIsCapped() {
        Id accountId = [SELECT Id FROM Account LIMIT 1].Id;
        Test.startTest();
        List<Task> timeline =
            FidelityActivityTimelineController.loadTimeline(accountId);
        Test.stopTest();
        System.assertLessThanOrEqual(200, timeline.size());
    }
}
