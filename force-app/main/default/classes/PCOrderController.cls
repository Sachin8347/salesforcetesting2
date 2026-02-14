public with sharing class PCOrderController {
    
    @AuraEnabled
    public static Account createPCOrder(String orderData) {
        try {
            // Parse the JSON order data
            Map<String, Object> orderMap = (Map<String, Object>)JSON.deserializeUntyped(orderData);
            
            // Create Account record to represent the PC Order
            Account newOrder = new Account();
            newOrder.Name = (String)orderMap.get('companyName') + ' - PC Order';
            newOrder.Description = 'Department: ' + (String)orderMap.get('department') + 
                                   '\nContact Email: ' + (String)orderMap.get('contactEmail') +
                                   '\nAdditional Requirements: ' + (String)orderMap.get('additionalRequirements');
            
            // Add device information to description
            List<Object> devices = (List<Object>)orderMap.get('devices');
            String deviceInfo = '\n\nDevices Ordered:\n';
            
            for (Object deviceObj : devices) {
                Map<String, Object> device = (Map<String, Object>)deviceObj;
                deviceInfo += '- ' + (String)device.get('label') + ' (Qty: ' + (Integer)device.get('quantity') + ')\n';
            }
            
            newOrder.Description += deviceInfo;
            newOrder.Type = 'PC Order';
            
            // Insert the order
            insert newOrder;
            
            return newOrder;
            
        } catch (Exception e) {
            throw new AuraHandledException('Error creating PC Order: ' + e.getMessage());
        }
    }
}
