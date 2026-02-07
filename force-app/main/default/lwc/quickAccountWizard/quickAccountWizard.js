import { LightningElement, track } from 'lwc';
import createAccount from '@salesforce/apex/QuickAccountController.createAccount';

export default class QuickAccountWizard extends LightningElement {
    @track successMessage = '';
    @track errorMessage = '';

    // Form Data
    @track formData = {
        name: '',
        accNumber: '',
        phone: '',
        website: '',
        industry: '',
        revenue: null,
        employees: null,
        city: ''
    };

    get industryOptions() {
        return [
            { label: 'Technology', value: 'Technology' },
            { label: 'Finance', value: 'Finance' },
            { label: 'Healthcare', value: 'Healthcare' },
            { label: 'Retail', value: 'Retail' }
        ];
    }

    // --- NEW LOGIC: Button State ---
    get isSaveDisabled() {
        // 1. Name is mandatory
        if (!this.formData.name) return true;

        // 2. Revenue must be >= 10,000,000
        // If revenue is missing OR less than 10M, disable button
        // if (!this.formData.revenue || this.formData.revenue < 10000000) {
        //     return true;
        // }

        return false;
    }

    handleInputChange(event) {
        const fieldMap = {
            'accName': 'name',
            'accNumber': 'accNumber',
            'accPhone': 'phone',
            'accWebsite': 'website',
            'accIndustry': 'industry',
            'accRevenue': 'revenue',
            'accEmployees': 'employees',
            'accCity': 'city'
        };

        const fieldId = event.target.dataset.id;
        const key = fieldMap[fieldId];
        
        if (key) {
            this.formData[key] = event.target.value;
            
            //Optional: Show immediate error on the field for better screenshot
            // if (fieldId === 'accRevenue') {
            //     const inputCmp = this.template.querySelector('[data-id="accRevenue"]');
            //     if (this.formData.revenue < 10000000) {
            //         inputCmp.setCustomValidity("Revenue must be $10M+ for Enterprise Accounts.");
            //     } else {
            //         inputCmp.setCustomValidity("");
            //     }
            //     inputCmp.reportValidity();
            // }
        }
    }

    handleCreate() {
        this.successMessage = '';
        this.errorMessage = '';

        // Double check (redundant but safe)
        if (this.isSaveDisabled) return;

        createAccount({ 
            name: this.formData.name,
            accNumber: this.formData.accNumber,
            phone: this.formData.phone,
            website: this.formData.website,
            industry: this.formData.industry,
            revenue: this.formData.revenue,
            employees: this.formData.employees,
            city: this.formData.city
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