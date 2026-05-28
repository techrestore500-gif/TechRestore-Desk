import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { fetchTicket } from '../api/tickets';
import IntakePrintPage from './IntakePrintPage';

vi.mock('../api/tickets', () => ({
    fetchTicket: vi.fn(),
}));

describe('IntakePrintPage', () => {
    it('renders intake details for a ticket', async () => {
        vi.mocked(fetchTicket).mockResolvedValue({
            id: 9,
            ticket_number: 'TR-00009',
            customer_id: 3,
            customer_name: 'Intake Customer',
            customer_phone: '555-1212',
            customer_alternate_phone: null,
            device_model_id: null,
            device_model_text_override: null,
            device_label: 'Galaxy S22',
            carrier: 'Unlocked',
            sim_type: 'Nano SIM',
            imei_serial: 'IMEI-123',
            device_color: 'Black',
            filter_status: 'Removed',
            issue_category: 'Battery',
            issue_description: 'Battery drains quickly',
            condition_summary: 'Back glass cracked',
            water_damage_status: 'no',
            dropped_status: 'yes',
            powers_on_status: 'yes',
            charges_status: 'yes',
            customer_approval_limit: 150,
            must_call_before_repair: true,
            customer_prefers_replacement_if_high: false,
            estimated_price: 119,
            final_price: null,
            payment_status: 'unpaid',
            diagnostic_fee: 35,
            status: 'New Intake',
            priority: 'normal',
            intake_staff: 'Taylor',
            assigned_technician: null,
            intake_date: new Date().toISOString(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            history: [],
            notes: [],
            repair_actions: [],
        });

        render(
            <MemoryRouter initialEntries={['/tickets/9/intake-print']}>
                <Routes>
                    <Route path="/tickets/:ticketId/intake-print" element={<IntakePrintPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByText('Intake form')).toBeInTheDocument();
        expect(screen.getByText('TR-00009')).toBeInTheDocument();
        expect(screen.getByText('Galaxy S22')).toBeInTheDocument();
        expect(screen.getByText('Battery drains quickly')).toBeInTheDocument();
        expect(screen.getByText('Customer signature')).toBeInTheDocument();

        await waitFor(() => {
            expect(fetchTicket).toHaveBeenCalledWith('9');
        });
    });
});