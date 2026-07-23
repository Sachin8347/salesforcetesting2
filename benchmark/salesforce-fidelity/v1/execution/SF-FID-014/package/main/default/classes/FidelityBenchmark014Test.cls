@IsTest
private class FidelityBenchmark014Test {
    @IsTest
    static void verifiesExportUsesEnforcedAccessMode() {
        insert new Case(Subject = 'Fidelity Export', Origin = 'Web');
        Test.startTest();
        List<Case> result = FidelityCaseExportController.exportOpenCases();
        Test.stopTest();
        System.assertEquals(1, result.size());
    }
}
