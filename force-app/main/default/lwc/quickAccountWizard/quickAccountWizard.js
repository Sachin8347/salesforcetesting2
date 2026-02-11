import { LightningElement, track } from 'lwc';

import createAccount from '@salesforce/apex/QuickAccountController.createAccount';

export default class QuickAccountWizard extends LightningElement {
    @track successMessage = '';
    @track errorMessage = '';

    formData = {
        name: '',
        accNumber: '',
        phone: '',
        website: '',
        industry: '',
        revenue: '', 
        revenueRange: '',
        employees: null,
        city: '',
        state: '',
        postalCode: '',
        country: '',
        type: '',
        description: '',
        primaryContact: '',
        contactTitle: '',
        contactEmail: '',
        contactPhone: '',
        fax: '',
        rating: '',
        customerPriority: '',
        slaExpiration: '',
        ticker: '',
        ownership: '',
        sicCode: '',
        yearStarted: '',
        marketCap: '',
        locations: null,
        fiscalYear: '',
        currency: '',
        stockExchange: '',
        dunsNumber: '',
        naicsCode: '',
        source: '',
        campaign: '',
        leadSource: '',
        lastActivityDate: '',
        nextActivityDate: '',
        activityType: '',
        activityDescription: ''
    };

    // REMOVED: get industryOptions() {...} is no longer needed

    handleInputChange(event) {
        const fieldMap = {
            'accName': 'name',
            'accNumber': 'accNumber',
            'accPhone': 'phone',
            'accWebsite': 'website',
            'accIndustry': 'industry',
            'accRevenue': 'revenue',
            'accRevenueRange': 'revenueRange',
            'accEmployees': 'employees',
            'accCity': 'city',
            'accState': 'state',
            'accPostalCode': 'postalCode',
            'accCountry': 'country',
            'accType': 'type',
            'accDescription': 'description',
            'accPrimaryContact': 'primaryContact',
            'accContactTitle': 'contactTitle',
            'accContactEmail': 'contactEmail',
            'accContactPhone': 'contactPhone',
            'accFax': 'fax',
            'accRating': 'rating',
            'accCustomerPriority': 'customerPriority',
            'accSlaExpiration': 'slaExpiration',
            'accTicker': 'ticker',
            'accOwnership': 'ownership',
            'accSicCode': 'sicCode',
            'accYearStarted': 'yearStarted',
            'accMarketCap': 'marketCap',
            'accLocations': 'locations',
            'accFiscalYear': 'fiscalYear',
            'accCurrency': 'currency',
            'accStockExchange': 'stockExchange',
            'accDunsNumber': 'dunsNumber',
            'accNaicsCode': 'naicsCode',
            'accSource': 'source',
            'accCampaign': 'campaign',
            'accLeadSource': 'leadSource',
            'accLastActivityDate': 'lastActivityDate',
            'accNextActivityDate': 'nextActivityDate',
            'accActivityType': 'activityType',
            'accActivityDescription': 'activityDescription'
        };

        const fieldId = event.target.dataset.id;
        const key = fieldMap[fieldId];
        
        if (key) {
            this.formData[key] = event.target.value;
        }
    }

    handleCreate() {
        this.successMessage = '';
        this.errorMessage = '';

        const nameInput = this.template.querySelector('[data-id="accName"]');
        if (!this.formData.name) {
            nameInput.setCustomValidity("Account Name is required.");
            nameInput.reportValidity();
            return;
        } else {
            nameInput.setCustomValidity("");
            nameInput.reportValidity();
        }

        // Clean Revenue Logic
        let cleanRevenue = 0;
        if (this.formData.revenue) {
            const stringVal = String(this.formData.revenue).replace(/[^0-9.]/g, '');
            cleanRevenue = parseFloat(stringVal);
        }

        createAccount({ 
            name: this.formData.name,
            accNumber: this.formData.accNumber,
            phone: this.formData.phone,
            website: this.formData.website,
            industry: this.formData.industry,
            revenue: cleanRevenue,
            revenueRange: this.formData.revenueRange,
            employees: this.formData.employees,
            city: this.formData.city,
            state: this.formData.state,
            postalCode: this.formData.postalCode,
            country: this.formData.country,
            type: this.formData.type,
            description: this.formData.description,
            primaryContact: this.formData.primaryContact,
            contactTitle: this.formData.contactTitle,
            contactEmail: this.formData.contactEmail,
            contactPhone: this.formData.contactPhone,
            fax: this.formData.fax,
            rating: this.formData.rating,
            customerPriority: this.formData.customerPriority,
            slaExpiration: this.formData.slaExpiration,
            ticker: this.formData.ticker,
            ownership: this.formData.ownership,
            sicCode: this.formData.sicCode,
            yearStarted: this.formData.yearStarted,
            marketCap: this.formData.marketCap,
            locations: this.formData.locations,
            fiscalYear: this.formData.fiscalYear,
            currency: this.formData.currency,
            stockExchange: this.formData.stockExchange,
            dunsNumber: this.formData.dunsNumber,
            naicsCode: this.formData.naicsCode,
            source: this.formData.source,
            campaign: this.formData.campaign,
            leadSource: this.formData.leadSource,
            lastActivityDate: this.formData.lastActivityDate,
            nextActivityDate: this.formData.nextActivityDate,
            activityType: this.formData.activityType,
            activityDescription: this.formData.activityDescription
        })
        .then(result => {
            this.successMessage = `Account "${result.Name}" created successfully!`;
            this.template.querySelectorAll('lightning-input, lightning-combobox').forEach(input => {
                input.value = null;
            });
            this.formData = {}; 
        })
        .catch(error => {
            this.errorMessage = 'Error: ' + (error.body ? error.body.message : error.message);
        });
    }
}