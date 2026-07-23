global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        Case record = new Case(
            Subject = 'Fidelity UI Export',
            Origin = 'Web'
        );
        insert record;
        return new Map<String, Object>{'caseId' => record.Id};
    }

    global static Map<String, Object> run() {
        List<Case> result = FidelityCaseExportController.exportOpenCases();
        return new Map<String, Object>{'resultCount' => result.size()};
    }
}
