global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        Account record = new Account(Name = 'Fidelity UI Null Guard');
        insert record;
        return new Map<String, Object>{'accountId' => record.Id};
    }

    global static Map<String, Object> run() {
        Integer beforeQueries = Limits.getQueries();
        String exceptionType;
        try {
            FidelityNullGuardController.loadAccount(null);
        } catch (Exception error) {
            exceptionType = error.getTypeName();
        }
        return new Map<String, Object>{
            'exceptionType' => exceptionType,
            'queryDelta' => Limits.getQueries() - beforeQueries
        };
    }
}
