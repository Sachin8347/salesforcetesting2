@IsTest
private class FidelityBenchmark010Test {
    private class GatewayMock implements HttpCalloutMock {
        public HttpResponse respond(HttpRequest request) {
            HttpResponse response = new HttpResponse();
            response.setStatusCode(202);
            response.setBody('{"accepted":true}');
            return response;
        }
    }

    @TestSetup
    static void seed() {
        insert new Opportunity(
            Name = 'Fidelity Invoice',
            StageName = 'Prospecting',
            CloseDate = Date.today().addDays(30)
        );
    }

    @IsTest
    static void verifiesCalloutBeforeDml() {
        Opportunity opportunityRecord = [
            SELECT Id, Description FROM Opportunity LIMIT 1
        ];
        Test.setMock(HttpCalloutMock.class, new GatewayMock());
        Test.startTest();
        HttpResponse response =
            FidelityInvoiceCalloutService.sendInvoice(opportunityRecord);
        Test.stopTest();
        System.assertEquals(202, response.getStatusCode());
        System.assertEquals(
            'Invoice queued',
            [SELECT Description FROM Opportunity WHERE Id = :opportunityRecord.Id].Description
        );
    }
}
