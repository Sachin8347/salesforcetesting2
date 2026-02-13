import { LightningElement, track, api } from 'lwc';
import createEventApplication from '@salesforce/apex/EventApplicationController.createEventApplication';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class EventApplicationForm extends LightningElement {
    @api title = 'Event Application Form';
    @track message = '';
    @track messageType = '';

    // Event type options
    eventTypeOptions = [
        { label: 'Conference', value: 'conference' },
        { label: 'Workshop', value: 'workshop' },
        { label: 'Seminar', value: 'seminar' },
        { label: 'Training', value: 'training' },
        { label: 'Meeting', value: 'meeting' },
        { label: 'Social Event', value: 'social_event' },
        { label: 'Other', value: 'other' }
    ];

    // Requirement options
    requirementOptions = [
        { label: 'Audio/Visual Equipment', value: 'av_equipment' },
        { label: 'Catering Service', value: 'catering' },
        { label: 'Parking Space', value: 'parking' },
        { label: 'WiFi Access', value: 'wifi' },
        { label: 'Security Personnel', value: 'security' },
        { label: 'Signage/Branding', value: 'signage' }
    ];

    @track formData = {
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        company: '',
        eventType: '',
        eventName: '',
        eventDate: '',
        expectedAttendees: '',
        eventDescription: '',
        additionalRequirements: ''
    };

    @track selectedRequirements = [];

    get messageClass() {
        return this.messageType === 'success' 
            ? 'slds-text-color_success' 
            : 'slds-text-color_error';
    }

    get messageIcon() {
        return this.messageType === 'success' 
            ? 'utility:success' 
            : 'utility:error';
    }

    handleInputChange(event) {
        const field = event.target.dataset.id;
        const value = event.target.value;
        this.formData = { ...this.formData, [field]: value };
    }

    handleEventTypeChange(event) {
        this.formData.eventType = event.detail.value;
    }

    handleRequirementsChange(event) {
        this.selectedRequirements = event.detail.value;
    }

    validateForm() {
        const requiredFields = ['firstName', 'lastName', 'email', 'eventType', 'eventName', 'eventDate'];
        
        for (const field of requiredFields) {
            if (!this.formData[field]) {
                this.message = `Please fill in the required field: ${this.getFieldLabel(field)}`;
                this.messageType = 'error';
                return false;
            }
        }

        // Email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(this.formData.email)) {
            this.message = 'Please enter a valid email address';
            this.messageType = 'error';
            return false;
        }

        return true;
    }

    getFieldLabel(field) {
        const labels = {
            firstName: 'First Name',
            lastName: 'Last Name',
            email: 'Email',
            eventType: 'Event Type',
            eventName: 'Event Name',
            eventDate: 'Event Date'
        };
        return labels[field] || field;
    }

    handleSubmitApplication() {
        if (!this.validateForm()) {
            return;
        }

        // Prepare application data
        const applicationData = {
            ...this.formData,
            requirements: this.selectedRequirements,
            expectedAttendees: parseInt(this.formData.expectedAttendees) || 0
        };

        // Call Apex method
        createEventApplication({ applicationData: JSON.stringify(applicationData) })
            .then(result => {
                this.message = `Success! Event application created: ${result.Name}`;
                this.messageType = 'success';
                this.dispatchEvent(
                    new ShowToastEvent({
                        title: 'Success',
                        message: 'Event application submitted successfully!',
                        variant: 'success'
                    })
                );
                this.resetForm();
            })
            .catch(error => {
                this.message = 'Error submitting application';
                this.messageType = 'error';
                this.dispatchEvent(
                    new ShowToastEvent({
                        title: 'Error',
                        message: error.body.message,
                        variant: 'error'
                    })
                );
            });
    }

    handleClearForm() {
        this.resetForm();
        this.message = 'Form cleared';
        this.messageType = 'success';
    }

    resetForm() {
        this.formData = {
            firstName: '',
            lastName: '',
            email: '',
            phone: '',
            company: '',
            eventType: '',
            eventName: '',
            eventDate: '',
            expectedAttendees: '',
            eventDescription: '',
            additionalRequirements: ''
        };
        this.selectedRequirements = [];
        this.message = '';
        this.messageType = '';
    }
}
