public with sharing class FidelityEventConsumer {
    public static void consume(List<Map<String, Object>> events) {
        List<Case> casesToInsert = new List<Case>();
        for (Map<String, Object> eventRecord : events) {
            casesToInsert.add(new Case(
                Subject = String.valueOf(eventRecord.get('subject')),
                Origin = 'Web'
            ));
        }
        insert casesToInsert;
    }
}
