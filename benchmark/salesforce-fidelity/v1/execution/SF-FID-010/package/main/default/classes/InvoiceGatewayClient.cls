public with sharing class InvoiceGatewayClient {
    public static HttpResponse send(Id opportunityId) {
        HttpRequest request = new HttpRequest();
        request.setEndpoint('callout:InvoiceGateway/invoices');
        request.setMethod('POST');
        request.setBody(JSON.serialize(new Map<String, Object>{'opportunityId' => opportunityId}));
        return new Http().send(request);
    }
}
