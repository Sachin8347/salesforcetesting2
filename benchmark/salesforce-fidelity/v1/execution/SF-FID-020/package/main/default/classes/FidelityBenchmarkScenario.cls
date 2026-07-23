global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        return new Map<String, Object>{'eventUuid' => 'evt-fidelity-ui-020'};
    }

    global static Map<String, Object> run() {
        Map<String, Object> eventRecord = new Map<String, Object>{
            'eventUuid' => 'evt-fidelity-ui-020',
            'subject' => 'Fidelity UI replay'
        };
        FidelityEventConsumer.consume(
            new List<Map<String, Object>>{eventRecord, eventRecord}
        );
        return new Map<String, Object>{
            'persistedCount' => [
                SELECT COUNT() FROM Case
                WHERE External_Event_Id__c = 'evt-fidelity-ui-020'
            ]
        };
    }
}
