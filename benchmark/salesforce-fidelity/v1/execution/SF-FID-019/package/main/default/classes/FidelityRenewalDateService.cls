public with sharing class FidelityRenewalDateService {
    public static Date renewalDate(Datetime contractEnd) {
        return contractEnd.date();
    }
}
