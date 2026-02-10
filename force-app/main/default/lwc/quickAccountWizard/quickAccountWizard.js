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
        employees: null,
        city: '',
        state: '',
        postalCode: '',
        type: '',
        description: '',
        ticker: '',
        ownership: '',
        sicCode: '',
        yearStarted: null
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
            'accEmployees': 'employees',
            'accCity': 'city',
            'accState': 'state',
            'accPostalCode': 'postalCode',
            'accType': 'type',
            'accDescription': 'description',
            'accTicker': 'ticker',
            'accOwnership': 'ownership',
            'accSicCode': 'sicCode',
            'accYearStarted': 'yearStarted'
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
            employees: this.formData.employees,
            city: this.formData.city,
            state: this.formData.state,
            postalCode: this.formData.postalCode,
            type: this.formData.type,
            description: this.formData.description,
            ticker: this.formData.ticker,
            ownership: this.formData.ownership,
            sicCode: this.formData.sicCode,
            yearStarted: this.formData.yearStarted
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