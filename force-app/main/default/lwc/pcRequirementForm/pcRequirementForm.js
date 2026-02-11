import { LightningElement, track } from 'lwc';

export default class PcRequirementForm extends LightningElement {
    @track successMessage = '';
    @track errorMessage = '';

    formData = {
        companyName: '',
        employeeCount: null,
        budget: null,
        contactName: '',
        contactEmail: '',
        contactPhone: '',
        machineType: '',
        ram: '',
        storage: '',
        osPreference: '',
        quantity: null,
        usageType: '',
        softwareNeeds: '',
        additionalNotes: ''
    };

    get machineTypeOptions() {
        return [
            { label: 'MacBook Air', value: 'macbook_air' },
            { label: 'MacBook Pro', value: 'macbook_pro' },
            { label: 'Mac mini', value: 'mac_mini' },
            { label: 'iMac', value: 'imac' },
            { label: 'Windows Laptop', value: 'windows_laptop' },
            { label: 'Windows Desktop', value: 'windows_desktop' }
        ];
    }

    get ramOptions() {
        return [
            { label: '8 GB', value: '8' },
            { label: '16 GB', value: '16' },
            { label: '32 GB', value: '32' },
            { label: '64 GB', value: '64' }
        ];
    }

    get storageOptions() {
        return [
            { label: '256 GB', value: '256' },
            { label: '512 GB', value: '512' },
            { label: '1 TB', value: '1024' },
            { label: '2 TB', value: '2048' }
        ];
    }

    get osOptions() {
        return [
            { label: 'macOS', value: 'macos' },
            { label: 'Windows', value: 'windows' },
            { label: 'Linux', value: 'linux' },
            { label: 'Mixed', value: 'mixed' }
        ];
    }

    get usageOptions() {
        return [
            { label: 'General Office / Business', value: 'office' },
            { label: 'Software Development', value: 'development' },
            { label: 'Design / Video / Media', value: 'design' },
            { label: 'Data / Analytics', value: 'data' },
            { label: 'Mixed Usage', value: 'mixed' }
        ];
    }

    handleInputChange(event) {
        const fieldId = event.target.dataset.id;
        if (fieldId && Object.prototype.hasOwnProperty.call(this.formData, fieldId)) {
            this.formData[fieldId] = event.target.value;
        }
    }

    handleReset() {
        this.formData = {
            companyName: '',
            employeeCount: null,
            budget: null,
            contactName: '',
            contactEmail: '',
            contactPhone: '',
            machineType: '',
            ram: '',
            storage: '',
            osPreference: '',
            quantity: null,
            usageType: '',
            softwareNeeds: '',
            additionalNotes: ''
        };
        this.successMessage = '';
        this.errorMessage = '';
    }

    handleSubmit() {
        this.successMessage = '';
        this.errorMessage = '';

        if (!this.formData.companyName || !this.formData.contactName || !this.formData.contactEmail) {
            this.errorMessage = 'Please fill in at least Company Name, Contact Name, and Contact Email.';
            return;
        }

        // In a real implementation, you would call an Apex method here to persist the request.
        // For now, just show a success message so the form is usable in any org.
        this.successMessage = 'PC requirements submitted successfully. Our team will review the details.';
    }
}
