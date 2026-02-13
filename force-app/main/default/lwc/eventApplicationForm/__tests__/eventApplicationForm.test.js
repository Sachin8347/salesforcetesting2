import { createElement } from 'lwc';
import EventApplicationForm from 'c/eventApplicationForm';

describe('c-event-application-form', () => {
    afterEach(() => {
        // The jsdom instance is shared across test cases in a single file so reset the DOM
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
    });

    it('renders the component with correct title', () => {
        const element = createElement('c-event-application-form', {
            is: EventApplicationForm
        });
        document.body.appendChild(element);

        const cardTitle = element.shadowRoot.querySelector('lightning-card');
        expect(cardTitle.title).toBe('Event Application Form');
    });

    it('validates required fields', () => {
        const element = createElement('c-event-application-form', {
            is: EventApplicationForm
        });
        document.body.appendChild(element);

        // Try to submit without filling required fields
        const submitButton = element.shadowRoot.querySelector('lightning-button[variant="brand"]');
        submitButton.click();

        // Should show error message
        const messageElement = element.shadowRoot.querySelector('.slds-text-color_error');
        expect(messageElement).toBeTruthy();
        expect(element.message).toContain('Please fill in the required field');
    });

    it('validates email format', () => {
        const element = createElement('c-event-application-form', {
            is: EventApplicationForm
        });
        document.body.appendChild(element);

        // Set invalid email
        element.formData.email = 'invalid-email';
        
        // Try to submit
        element.handleSubmitApplication();

        // Should show email validation error
        expect(element.message).toBe('Please enter a valid email address');
        expect(element.messageType).toBe('error');
    });

    it('clears form when clear button is clicked', () => {
        const element = createElement('c-event-application-form', {
            is: EventApplicationForm
        });
        document.body.appendChild(element);

        // Fill some data
        element.formData.firstName = 'John';
        element.formData.lastName = 'Doe';
        element.formData.email = 'john.doe@example.com';

        // Click clear button
        const clearButton = element.shadowRoot.querySelector('lightning-button[variant="neutral"]');
        clearButton.click();

        // Form should be reset
        expect(element.formData.firstName).toBe('');
        expect(element.formData.lastName).toBe('');
        expect(element.formData.email).toBe('');
        expect(element.message).toBe('Form cleared');
        expect(element.messageType).toBe('success');
    });

    it('has correct event type options', () => {
        const element = createElement('c-event-application-form', {
            is: EventApplicationForm
        });
        document.body.appendChild(element);

        const expectedOptions = [
            { label: 'Conference', value: 'conference' },
            { label: 'Workshop', value: 'workshop' },
            { label: 'Seminar', value: 'seminar' },
            { label: 'Training', value: 'training' },
            { label: 'Meeting', value: 'meeting' },
            { label: 'Social Event', value: 'social_event' },
            { label: 'Other', value: 'other' }
        ];

        expect(element.eventTypeOptions).toEqual(expectedOptions);
    });

    it('has correct requirement options', () => {
        const element = createElement('c-event-application-form', {
            is: EventApplicationForm
        });
        document.body.appendChild(element);

        const expectedOptions = [
            { label: 'Audio/Visual Equipment', value: 'av_equipment' },
            { label: 'Catering Service', value: 'catering' },
            { label: 'Parking Space', value: 'parking' },
            { label: 'WiFi Access', value: 'wifi' },
            { label: 'Security Personnel', value: 'security' },
            { label: 'Signage/Branding', value: 'signage' }
        ];

        expect(element.requirementOptions).toEqual(expectedOptions);
    });
});
