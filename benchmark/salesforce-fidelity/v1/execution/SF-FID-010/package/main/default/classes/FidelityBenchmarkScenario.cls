global with sharing class FidelityBenchmarkScenario {
    global static Map<String, Object> seed() {
        Opportunity record = new Opportunity(
            Name = 'Fidelity UI Invoice',
            StageName = 'Prospecting',
            CloseDate = Date.today().addDays(30)
        );
        insert record;
        return new Map<String, Object>{'opportunityId' => record.Id};
    }

    global static Map<String, Object> run() {
        Opportunity record = [
            SELECT Id, Description FROM Opportunity
            WHERE Name = 'Fidelity UI Invoice' LIMIT 1
        ];
        HttpResponse response = FidelityInvoiceCalloutService.sendInvoice(record);
        return new Map<String, Object>{
            'statusCode' => response.getStatusCode(),
            'description' => [
                SELECT Description FROM Opportunity WHERE Id = :record.Id
            ].Description
        };
    }
}
