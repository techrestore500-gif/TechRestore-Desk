import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { fetchLoanerAgreement } from '../api/tickets';
import { fetchLoanerAgreementDefaults } from '../api/system';
import LoanerAgreementPrintPage from './LoanerAgreementPrintPage';

vi.mock('../api/tickets', () => ({
    fetchLoanerAgreement: vi.fn(),
}));

vi.mock('../api/system', () => ({
    fetchLoanerAgreementDefaults: vi.fn(),
}));

describe('LoanerAgreementPrintPage', () => {
    it('renders the latest loaner agreement for a ticket', async () => {
        vi.mocked(fetchLoanerAgreementDefaults).mockResolvedValue({
            responsibility_text: 'Custom responsibility text.',
            return_policy_text: 'Custom return policy text.',
            signature_note_text: 'Custom signature note.',
            updated_at: new Date().toISOString(),
        });

        vi.mocked(fetchLoanerAgreement).mockResolvedValue({
            id: 5,
            ticket_id: 14,
            ticket_number: 'TR-00014',
            customer_id: 2,
            customer_name: 'Loaner Customer',
            customer_phone: '555-4444',
            device_label: 'iPhone 13',
            issue_category: 'Screen',
            loaner_phone_id: 3,
            loaner_code: 'L-0003',
            loaner_device_label: 'Apple iPhone 8',
            date_out: new Date().toISOString(),
            expected_return_date: new Date().toISOString(),
            condition_out: 'Clean with minor wear',
            charger_included: true,
            sim_moved: true,
            outgoing_call_tested: true,
            incoming_call_tested: true,
            deposit_amount: 50,
            agreement_signed: true,
            checkout_staff: 'Alex',
            status: 'Checked Out',
        });

        render(
            <MemoryRouter initialEntries={['/tickets/14/loaner-agreement']}>
                <Routes>
                    <Route path="/tickets/:ticketId/loaner-agreement" element={<LoanerAgreementPrintPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByText('Loaner agreement')).toBeInTheDocument();
        expect(screen.getByText('TR-00014')).toBeInTheDocument();
        expect(screen.getByText(/L-0003/)).toBeInTheDocument();
        expect(screen.getByText('$50.00')).toBeInTheDocument();
        expect(screen.getByText('Custom responsibility text.')).toBeInTheDocument();
        expect(screen.getByText('Customer signature')).toBeInTheDocument();

        await waitFor(() => {
            expect(fetchLoanerAgreement).toHaveBeenCalledWith('14');
        });
    });
});