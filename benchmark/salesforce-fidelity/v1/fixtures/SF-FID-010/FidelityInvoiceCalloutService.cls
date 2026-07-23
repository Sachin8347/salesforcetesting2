public with sharing class FidelityInvoiceCalloutService {
    public static HttpResponse sendInvoice(Opportunity opportunityRecord) {
        opportunityRecord.Description = 'Invoice queued';
        update opportunityRecord;
        HttpRequest request = new HttpRequest();
        request.setEndpoint('callout:InvoiceGateway/invoices');
        request.setMethod('POST');
        return new Http().send(request);
    }
}
