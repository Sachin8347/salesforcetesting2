import { LightningElement, track, api } from 'lwc';
import createPCOrder from '@salesforce/apex/PCOrderController.createPCOrder';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class PcOrderWizard extends LightningElement {
    @api title = 'PC Order Wizard';
    @track message = '';
    @track messageType = '';

    // Device options
    macOptions = [
        { label: 'MacBook Air M2', value: 'macbook_air_m2' },
        { label: 'MacBook Pro M2', value: 'macbook_pro_m2' },
        { label: 'Mac Studio', value: 'mac_studio' },
        { label: 'iMac 24"', value: 'imac_24' },
        { label: 'Mac mini', value: 'mac_mini' }
    ];

    windowsOptions = [
        { label: 'Dell Latitude Laptop', value: 'dell_latitude' },
        { label: 'HP EliteBook Laptop', value: 'hp_elitebook' },
        { label: 'Lenovo ThinkPad', value: 'lenovo_thinkpad' },
        { label: 'Dell OptiPlex Desktop', value: 'dell_optiplex' },
        { label: 'HP Elite Desktop', value: 'hp_elite_desktop' }
    ];

    @track selectedMacDevices = [];
    @track selectedWindowsDevices = [];
    @track deviceQuantities = [];

    get showQuantitySection() {
        return this.selectedMacDevices.length > 0 || this.selectedWindowsDevices.length > 0;
    }

    get messageClass() {
        return this.messageType === 'success' 
            ? 'slds-text-color_success' 
            : 'slds-text-color_error';
    }

    handleMacChange(event) {
        this.selectedMacDevices = event.detail.value;
        this.updateDeviceQuantities();
    }

    handleWindowsChange(event) {
        this.selectedWindowsDevices = event.detail.value;
        this.updateDeviceQuantities();
    }

    updateDeviceQuantities() {
        const allDevices = [...this.selectedMacDevices, ...this.selectedWindowsDevices];
        const allOptions = [...this.macOptions, ...this.windowsOptions];
        
        this.deviceQuantities = allDevices.map(deviceValue => {
            const option = allOptions.find(opt => opt.value === deviceValue);
            const existingQuantity = this.deviceQuantities.find(q => q.key === deviceValue);
            
            return {
                key: deviceValue,
                label: option ? option.label : deviceValue,
                quantity: existingQuantity ? existingQuantity.quantity : 1
            };
        });
    }

    handleQuantityChange(event) {
        const deviceKey = event.target.dataset.device;
        const quantity = parseInt(event.target.value) || 1;
        
        this.deviceQuantities = this.deviceQuantities.map(device => {
            if (device.key === deviceKey) {
                return { ...device, quantity };
            }
            return device;
        });
    }

    handlePlaceOrder() {
        // Get form values
        const companyInput = this.template.querySelector('[data-id="companyName"]');
        const departmentInput = this.template.querySelector('[data-id="department"]');
        const emailInput = this.template.querySelector('[data-id="contactEmail"]');
        const requirementsInput = this.template.querySelector('[data-id="additionalRequirements"]');
        
        const companyName = companyInput.value;
        const department = departmentInput.value;
        const contactEmail = emailInput.value;
        const additionalRequirements = requirementsInput.value;

        // Validation
        if (!companyName ) {
            if (!companyName) companyInput.reportValidity();
            
            return;
        }

        if (this.selectedMacDevices.length === 0 && this.selectedWindowsDevices.length === 0) {
            this.message = 'Please select at least one device';
            this.messageType = 'error';
            return;
        }

        // Prepare order data
        const orderData = {
            companyName,
            department,
            contactEmail,
            additionalRequirements,
            devices: this.deviceQuantities
        };

        // Call Apex method testededdddd
        createPCOrder({ orderData: JSON.stringify(orderData) })
            .then(result => {
                this.message = `Success! Order created: ${result.Name}`;
                this.messageType = 'success';
                this.dispatchEvent(
                    new ShowToastEvent({
                        title: 'Success',
                        message: 'PC Order placed successfully!',
                        variant: 'success'
                    })
                );
                this.resetForm();
            })
            .catch(error => {
                this.message = 'Error placing order';
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

    resetForm() {
        // Clear form inputs
        this.template.querySelector('[data-id="companyName"]').value = '';
        this.template.querySelector('[data-id="department"]').value = '';
        this.template.querySelector('[data-id="contactEmail"]').value = '';
        this.template.querySelector('[data-id="additionalRequirements"]').value = '';
        
        // Reset selections
        this.selectedMacDevices = [];
        this.selectedWindowsDevices = [];
        this.deviceQuantities = [];
    }
}
