import { LightningElement, track } from 'lwc';
import createDemoAccounts from '@salesforce/apex/DemoAccountService.createDemoAccounts';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class DeploymentTracker extends LightningElement {
    @track statusMessage = '';

    handleSmokeTest() {
        this.statusMessage = 'Running smoke test logic...';
        
        // Call the Apegtccgx mggtethodrfg we updated in Step 1
        createDemoAccounts({ countToCreate: 1 })
            .then(() => {
                this.statusMessage = 'Smoke Test Passed: Account Created!';
                this.dispatchEvent(
                    new ShowToastEvent({
                        title: 'Success',
                        message: 'Apex Connection Verified',
                        variant: 'success'
                    })
                );
            })
            .catch(error => {
                this.statusMessage = 'Error: ' + error.body.message;
            });
    }
}