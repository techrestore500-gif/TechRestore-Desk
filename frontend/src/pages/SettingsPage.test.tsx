import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
    createRepairCategory,
    fetchPricingRules,
    fetchRepairCategories,
    fetchStatusWorkflowRules,
    fetchSupportedModels,
    updateStatusWorkflowRules,
    updatePricingRules,
    updateRepairCategory,
} from '../api/tickets';
import {
    createDatabaseBackup,
    exportDataSnapshot,
    fetchLoanerAgreementDefaults,
    fetchNotificationTemplates,
    fetchSystemActivityHistory,
    fetchTwilioSetupStatus,
    fetchTwilioSettings,
    clearTwilioSettings,
    updateLoanerAgreementDefaults,
    updateNotificationTemplates,
    updateTwilioSettings,
} from '../api/system';
import SettingsPage from './SettingsPage';

vi.mock('../api/system', async () => {
    const actual = await vi.importActual<typeof import('../api/system')>('../api/system');
    return {
        ...actual,
        createDatabaseBackup: vi.fn(),
        exportDataSnapshot: vi.fn(),
        fetchLoanerAgreementDefaults: vi.fn(),
        fetchNotificationTemplates: vi.fn(),
        fetchSystemActivityHistory: vi.fn(),
        fetchTwilioSetupStatus: vi.fn(),
        fetchTwilioSettings: vi.fn(),
        clearTwilioSettings: vi.fn(),
        updateLoanerAgreementDefaults: vi.fn(),
        updateNotificationTemplates: vi.fn(),
        updateTwilioSettings: vi.fn(),
    };
});

vi.mock('../api/tickets', () => ({
    fetchPricingRules: vi.fn(),
    fetchSupportedModels: vi.fn(),
    fetchRepairCategories: vi.fn(),
    fetchStatusWorkflowRules: vi.fn(),
    createRepairCategory: vi.fn(),
    updateRepairCategory: vi.fn(),
    updateStatusWorkflowRules: vi.fn(),
    updatePricingRules: vi.fn(),
}));


async function renderSettingsPage() {
    render(<SettingsPage />);
    await screen.findByText('Shop info');
}


describe('SettingsPage', () => {
    beforeEach(() => {
        const storage = new Map<string, string>();

        Object.defineProperty(window, 'localStorage', {
            configurable: true,
            value: {
                getItem: (key: string) => storage.get(key) ?? null,
                setItem: (key: string, value: string) => {
                    storage.set(key, value);
                },
            },
        });

        Object.defineProperty(window.URL, 'createObjectURL', {
            configurable: true,
            value: vi.fn(() => 'blob:test-url'),
        });
        Object.defineProperty(window.URL, 'revokeObjectURL', {
            configurable: true,
            value: vi.fn(),
        });

        vi.mocked(fetchSystemActivityHistory).mockResolvedValue([]);
        vi.mocked(fetchTwilioSetupStatus).mockResolvedValue({
            twilio_credentials_configured: true,
            public_webhook_base_url_configured: true,
            voice_webhook_url: 'https://example.ngrok.app/api/twilio/voice',
            recording_callback_url: 'https://example.ngrok.app/api/twilio/recording',
            recording_callback_route_active: true,
            last_voicemail: {
                id: 9,
                caller_number: '+15555550999',
                called_number: '+15555550123',
                call_sid: 'CA999',
                recording_sid: 'RE999',
                recording_url: 'https://api.twilio.com/recordings/RE999',
                recording_duration_seconds: 21,
                transcription_text: null,
                notes: null,
                status: 'new',
                customer_id: null,
                customer_name: null,
                customer_phone: null,
                ticket_id: null,
                listened_at: null,
                archived_at: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        });
        vi.mocked(fetchTwilioSettings).mockResolvedValue({
            account_sid: 'TWILIO_ACCOUNT_SID_TEST_4',
            phone_number: '+15555550123',
            public_webhook_base_url: 'https://example.ngrok.app',
            voicemail_greeting: 'Thanks for calling Tech Restore',
            voicemail_greeting_audio_url: null,
            twilio_auth_token_set: true,
            configured: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
        });
        vi.mocked(clearTwilioSettings).mockResolvedValue({
            account_sid: null,
            phone_number: null,
            public_webhook_base_url: null,
            voicemail_greeting: null,
            voicemail_greeting_audio_url: null,
            twilio_auth_token_set: false,
            configured: false,
            created_at: null,
            updated_at: null,
        });
        vi.mocked(updateTwilioSettings).mockResolvedValue({
            account_sid: 'TWILIO_ACCOUNT_SID_TEST_4',
            phone_number: '+15555550123',
            public_webhook_base_url: 'https://example.ngrok.app',
            voicemail_greeting: 'Thanks for calling Tech Restore',
            voicemail_greeting_audio_url: null,
            twilio_auth_token_set: true,
            configured: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
        });
        vi.mocked(fetchLoanerAgreementDefaults).mockResolvedValue({
            responsibility_text: 'Customer accepts responsibility for the loaner device.',
            return_policy_text: 'Loaner must be returned at pickup closeout.',
            signature_note_text: 'Signatures confirm checkout terms.',
            updated_at: new Date().toISOString(),
        });
        vi.mocked(updateLoanerAgreementDefaults).mockResolvedValue({
            responsibility_text: 'Customer accepts responsibility for the loaner device.',
            return_policy_text: 'Loaner must be returned at pickup closeout.',
            signature_note_text: 'Signatures confirm checkout terms.',
            updated_at: new Date().toISOString(),
        });
        vi.mocked(fetchNotificationTemplates).mockResolvedValue([
            {
                id: 1,
                template_key: 'diagnosis_complete',
                template_name: 'Diagnosis complete – approval needed',
                description: 'Sent when diagnosis is complete and customer approval is needed',
                template_text: 'Hello, your [MODEL] diagnosis is complete. Estimated price: $[AMOUNT].',
                placeholders: ['MODEL', 'AMOUNT'],
                updated_at: new Date().toISOString(),
            },
            {
                id: 2,
                template_key: 'ready_for_pickup',
                template_name: 'Ready for pickup',
                description: 'Sent when the repaired device is ready',
                template_text: 'Your [MODEL] is ready for pickup. Amount due: $[AMOUNT].',
                placeholders: ['MODEL', 'AMOUNT', 'LOANER_ID'],
                updated_at: new Date().toISOString(),
            },
        ]);
        vi.mocked(updateNotificationTemplates).mockResolvedValue([
            {
                id: 1,
                template_key: 'diagnosis_complete',
                template_name: 'Diagnosis complete – approval needed',
                description: 'Sent when diagnosis is complete and customer approval is needed',
                template_text: 'Updated message text.',
                placeholders: ['MODEL', 'AMOUNT'],
                updated_at: new Date().toISOString(),
            },
            {
                id: 2,
                template_key: 'ready_for_pickup',
                template_name: 'Ready for pickup',
                description: 'Sent when the repaired device is ready',
                template_text: 'Your [MODEL] is ready for pickup. Amount due: $[AMOUNT].',
                placeholders: ['MODEL', 'AMOUNT', 'LOANER_ID'],
                updated_at: new Date().toISOString(),
            },
        ]);
        vi.mocked(fetchSupportedModels).mockResolvedValue([
            {
                id: 1,
                manufacturer: 'Apple',
                device_family: 'iPhone',
                model_name: 'iPhone 13',
                model_aliases: null,
                repair_policy: 'Standard',
                notes: null,
            },
        ]);
        vi.mocked(fetchPricingRules).mockResolvedValue({
            defaults: {
                base_labor_rate_per_hour: 85,
                minimum_labor_charge: 35,
                part_markup_percent: 20,
                diagnostic_fee: 35,
            },
            difficulty_multipliers: { easy: 1 },
            risk_multipliers: { low: 1 },
            repair_categories: [
                {
                    id: 1,
                    name: 'Battery swap',
                    description: 'Battery replacement and health verification',
                    default_policy: 'Standard',
                    requires_soldering: 0,
                },
            ],
        });
        vi.mocked(updatePricingRules).mockResolvedValue({
            defaults: {
                base_labor_rate_per_hour: 85,
                minimum_labor_charge: 35,
                part_markup_percent: 20,
                diagnostic_fee: 35,
            },
        });
        vi.mocked(fetchRepairCategories).mockResolvedValue([
            {
                id: 1,
                name: 'Battery swap',
                description: 'Battery replacement and health verification',
                default_policy: 'Standard',
                requires_soldering: false,
                active: true,
            },
        ]);
        vi.mocked(createRepairCategory).mockResolvedValue({
            id: 2,
            name: 'Face ID calibration',
            description: 'Sensor alignment',
            default_policy: 'Advanced',
            requires_soldering: false,
            active: true,
        });
        vi.mocked(updateRepairCategory).mockResolvedValue({
            id: 1,
            name: 'Battery swap',
            description: 'Battery replacement and health verification',
            default_policy: 'Standard',
            requires_soldering: false,
            active: false,
        });
        vi.mocked(fetchStatusWorkflowRules).mockResolvedValue({
            transitions: {
                'New Intake': ['Needs Diagnosis'],
                'Needs Diagnosis': ['Diagnosed'],
                Diagnosed: ['Approved'],
                Approved: ['Ready for Repair'],
                'Ready for Repair': ['In Repair'],
                'In Repair': ['Ready for Pickup'],
                'Ready for Pickup': ['Picked Up / Closed'],
                'Picked Up / Closed': [],
            },
            guardrails: {
                enforce_no_active_loaner_for_ready_for_pickup: true,
                enforce_no_active_loaner_for_closed_statuses: true,
                enforce_final_price_for_ready_for_pickup: true,
                enforce_final_price_for_closed_paid_statuses: true,
            },
            updated_at: new Date().toISOString(),
        });
        vi.mocked(updateStatusWorkflowRules).mockResolvedValue({
            transitions: {
                'New Intake': ['Needs Diagnosis'],
                'Needs Diagnosis': ['Diagnosed'],
                Diagnosed: ['Approved'],
                Approved: ['Ready for Repair'],
                'Ready for Repair': ['In Repair'],
                'In Repair': ['Ready for Pickup'],
                'Ready for Pickup': ['Picked Up / Closed'],
                'Picked Up / Closed': [],
            },
            guardrails: {
                enforce_no_active_loaner_for_ready_for_pickup: true,
                enforce_no_active_loaner_for_closed_statuses: true,
                enforce_final_price_for_ready_for_pickup: false,
                enforce_final_price_for_closed_paid_statuses: true,
            },
            updated_at: new Date().toISOString(),
        });
    });

    it('saves shop information to localStorage', async () => {
        await renderSettingsPage();

        fireEvent.change(screen.getByPlaceholderText('Tech Restore'), {
            target: { value: 'Tech Restore West' },
        });
        fireEvent.change(screen.getByPlaceholderText('(555) 000-0000'), {
            target: { value: '555-9000' },
        });
        fireEvent.change(screen.getByPlaceholderText('repairs@example.com'), {
            target: { value: 'west@techrestore.test' },
        });

        fireEvent.click(screen.getByRole('button', { name: 'Save shop info' }));

        await waitFor(() => {
            expect(JSON.parse(localStorage.getItem('techRestore.shopName') ?? 'null')).toBe('Tech Restore West');
            expect(JSON.parse(localStorage.getItem('techRestore.shopPhone') ?? 'null')).toBe('555-9000');
            expect(JSON.parse(localStorage.getItem('techRestore.shopEmail') ?? 'null')).toBe('west@techrestore.test');
        });
        expect(screen.getByText('Saved!')).toBeInTheDocument();
    });

    it('adds a technician to the roster', async () => {
        await renderSettingsPage();

        fireEvent.change(screen.getByPlaceholderText('Add technician name'), {
            target: { value: 'Jordan' },
        });
        fireEvent.click(screen.getByRole('button', { name: 'Add' }));

        expect(screen.getByText('Jordan')).toBeInTheDocument();
        expect(JSON.parse(localStorage.getItem('techRestore.techRoster') ?? '[]')).toContain('Jordan');
    });

    it('creates a backup and shows the resulting filename', async () => {
        vi.mocked(createDatabaseBackup).mockResolvedValue({
            file_name: 'backup-2026-05-10.sqlite',
            backup_path: 'C:/backups/backup-2026-05-10.sqlite',
            created_at: '2026-05-10T17:00:00Z',
            file_size_bytes: 1024,
        });

        await renderSettingsPage();

        fireEvent.click(screen.getByRole('button', { name: 'Create backup' }));

        await waitFor(() => {
            expect(createDatabaseBackup).toHaveBeenCalledTimes(1);
        });

        expect(await screen.findByText('Backup created: backup-2026-05-10.sqlite')).toBeInTheDocument();
    });

    it('exports a JSON snapshot', async () => {
        vi.mocked(exportDataSnapshot).mockResolvedValue({
            fileName: 'tech-restore-export.json',
            blob: new Blob(['{}'], { type: 'application/json' }),
        });

        const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => { });

        await renderSettingsPage();

        fireEvent.click(screen.getByRole('button', { name: 'Export JSON snapshot' }));

        await waitFor(() => {
            expect(exportDataSnapshot).toHaveBeenCalledTimes(1);
        });

        expect(clickSpy).toHaveBeenCalledTimes(1);
        expect(await screen.findByText('Export ready: tech-restore-export.json')).toBeInTheDocument();

        clickSpy.mockRestore();
    });

    it('renders recent system activity history', async () => {
        vi.mocked(fetchSystemActivityHistory).mockResolvedValue([
            {
                activity_type: 'backup',
                file_name: 'backup-2026-05-10.sqlite',
                created_at: '2026-05-10T17:00:00Z',
                file_size_bytes: 2048,
                file_path: 'C:/backups/backup-2026-05-10.sqlite',
            },
        ]);

        await renderSettingsPage();

        expect(await screen.findByText('Recent system activity')).toBeInTheDocument();
        expect(screen.getByText('backup-2026-05-10.sqlite')).toBeInTheDocument();
        expect(screen.getByText('Backup')).toBeInTheDocument();
    });

    it('renders supported devices and repair categories reference data', async () => {
        await renderSettingsPage();

        expect(await screen.findByText('Device & repair catalog')).toBeInTheDocument();
        expect(screen.getByText('1 models across 1 device families.')).toBeInTheDocument();
        expect(screen.getByText('iPhone')).toBeInTheDocument();
        expect(screen.getByText('Apple')).toBeInTheDocument();
        expect(screen.getAllByText('Battery swap').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Battery replacement and health verification').length).toBeGreaterThan(0);
    });

    it('renders Twilio settings with the auth token masked', async () => {
        await renderSettingsPage();

        expect(await screen.findByText('Phone / Twilio')).toBeInTheDocument();
        expect(await screen.findByText('Token stored')).toBeInTheDocument();
        expect(await screen.findByText('Test setup status')).toBeInTheDocument();
        expect(screen.getByText('Twilio credentials configured: OK')).toBeInTheDocument();
        expect(screen.getByText('Recording callback route active: OK')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Stored securely - enter a new token to replace it')).toHaveAttribute('type', 'password');
        fireEvent.click(screen.getByRole('button', { name: 'Show token' }));
        expect(screen.getByPlaceholderText('Stored securely - enter a new token to replace it')).toHaveAttribute('type', 'text');
    });

    it('saves pricing defaults through the API', async () => {
        await renderSettingsPage();

        const laborRateInput = await screen.findByLabelText('Labor rate ($/hr)');
        const diagnosticFeeInput = screen.getByLabelText('Diagnostic fee ($)');
        fireEvent.change(laborRateInput, { target: { value: '95' } });
        fireEvent.change(diagnosticFeeInput, { target: { value: '25' } });
        fireEvent.click(screen.getByRole('button', { name: 'Save pricing' }));

        await waitFor(() => {
            expect(updatePricingRules).toHaveBeenCalledWith({
                base_labor_rate_per_hour: 95,
                diagnostic_fee: 25,
            });
        });
    });

    it('creates a repair category from settings', async () => {
        await renderSettingsPage();

        fireEvent.change(await screen.findByPlaceholderText('Category name'), {
            target: { value: 'Face ID calibration' },
        });
        fireEvent.change(screen.getByPlaceholderText('Default policy'), {
            target: { value: 'Advanced' },
        });
        fireEvent.change(screen.getByPlaceholderText('Description'), {
            target: { value: 'Sensor and camera alignment workflow' },
        });
        fireEvent.click(screen.getByRole('button', { name: 'Add repair category' }));

        await waitFor(() => {
            expect(createRepairCategory).toHaveBeenCalledWith({
                name: 'Face ID calibration',
                description: 'Sensor and camera alignment workflow',
                default_policy: 'Advanced',
                requires_soldering: false,
            });
        });
    });

    it('toggles a repair category active state', async () => {
        await renderSettingsPage();

        fireEvent.click(await screen.findByRole('button', { name: 'Disable' }));

        await waitFor(() => {
            expect(updateRepairCategory).toHaveBeenCalledWith(1, { active: false });
        });
    });

    it('saves status workflow rules from settings', async () => {
        await renderSettingsPage();

        fireEvent.click(await screen.findByLabelText('Require final price before Ready for Pickup'));
        fireEvent.click(screen.getByRole('button', { name: 'Save workflow rules' }));

        await waitFor(() => {
            expect(updateStatusWorkflowRules).toHaveBeenCalled();
        });
    });

    it('saves loaner agreement defaults from settings', async () => {
        await renderSettingsPage();

        const responsibilityText = await screen.findByLabelText('Responsibility text');
        fireEvent.change(responsibilityText, {
            target: { value: 'Borrower is responsible for damage while checked out.' },
        });
        fireEvent.click(screen.getByRole('button', { name: 'Save loaner agreement defaults' }));

        await waitFor(() => {
            expect(updateLoanerAgreementDefaults).toHaveBeenCalledWith({
                responsibility_text: 'Borrower is responsible for damage while checked out.',
                return_policy_text: 'Loaner must be returned at pickup closeout.',
                signature_note_text: 'Signatures confirm checkout terms.',
            });
        });
    });

    it('saves notification templates from settings', async () => {
        await renderSettingsPage();

        const textareas = await screen.findAllByDisplayValue('Hello, your [MODEL] diagnosis is complete. Estimated price: $[AMOUNT].');
        expect(textareas.length).toBeGreaterThan(0);

        fireEvent.change(textareas[0], {
            target: { value: 'Custom diagnosis message with [MODEL] and [AMOUNT].' },
        });
        fireEvent.click(screen.getByRole('button', { name: 'Save notification templates' }));

        await waitFor(() => {
            expect(updateNotificationTemplates).toHaveBeenCalled();
        });
    });
});

