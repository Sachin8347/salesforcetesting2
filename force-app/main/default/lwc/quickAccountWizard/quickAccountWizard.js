import { LightningElement, track } from 'lwc';
import createAccount from '@salesforce/apex/QuickAccountController.createAccount';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class QuickAccountWizard extends LightningElement {
    @track message = '';
    
    // Track values to control button state
    @track name = '';
    @track phone = '';
    @track age = '';

    // Capture input changes in real-time
    handleInputChange(event) {
        const field = event.target.dataset.id;
        const val = event.target.value;

        if (field === 'accName') this.name = val;
        if (field === 'accPhone') this.phone = val;
        if (field === 'accAge') this.age = val;
    }

    // Button is disabled if ANY field is empty
    get isButtonDisabled() {
        return !(this.name && this.phone && this.age);
    }

    handleCreate() {
        // Double check validation (Redundant but safe)
        if (this.isButtonDisabled) return;

        createAccount({ name: this.name, phone: this.phone, age: parseInt(this.age) })
            .then(result => {
                this.message = `Success! Created account: ${result.Name}`;
                this.dispatchEvent(
                    new ShowToastEvent({
                        title: 'Success',
                        message: 'Account created successfully!',
                        variant: 'success'
                    })
                );
                // Clear state
                this.name = '';
                this.phone = '';
                this.age = '';
                // Clear UI inputs
                this.template.querySelectorAll('lightning-input').forEach(input => input.value = '');
            })
            //jknhjhjhbjbieuihguiheioghoeh
            .catch(error => {
                this.message = 'Error creating account';
                this.dispatchEvent(
                    new ShowToastEvent({
                        title: 'Error',
                        message: error.body.message,
                        variant: 'error'
                    })
                );
            });
    }
}