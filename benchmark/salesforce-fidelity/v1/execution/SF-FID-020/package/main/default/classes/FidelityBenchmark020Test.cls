@IsTest
private class FidelityBenchmark020Test {
    @IsTest
    static void verifiesReplayIsIdempotent() {
        Map<String, Object> eventRecord = new Map<String, Object>{
            'eventUuid' => 'evt-fidelity-020',
            'subject' => 'Fidelity replay'
        };
        Test.startTest();
        FidelityEventConsumer.consume(
            new List<Map<String, Object>>{eventRecord, eventRecord}
        );
        Test.stopTest();
        System.assertEquals(
            1,
            [SELECT COUNT() FROM Case
             WHERE External_Event_Id__c = 'evt-fidelity-020']
        );
    }
}
