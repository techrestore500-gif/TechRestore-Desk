import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { fetchTicket } from '../api/tickets';
import InvoicePrintPage from './InvoicePrintPage';

vi.mock('../api/tickets', () => ({
    fetchTicket: vi.fn(),
}));

describe('InvoicePrintPage', () => {
    it('renders invoice details for a ticket', async () => {
        vi.mocked(fetchTicket).mockResolvedValue({
            id: 14,
            ticket_number: 'TR-00014',
            customer_id: 2,
            customer_name: 'Invoice Customer',
            customer_phone: '555-6666',
            customer_alternate_phone: null,
            device_model_id: null,
            device_model_text_override: null,
            device_label: 'iPhone 13',
            carrier: null,
            sim_type: null,
            imei_serial: null,
            device_color: null,
            filter_status: null,
            issue_category: 'Screen',
            issue_description: null,
            condition_summary: null,
            water_damage_status: 'unknown',
            dropped_status: 'yes',
            powers_on_status: 'yes',
            charges_status: 'yes',
            customer_approval_limit: null,
            must_call_before_repair: false,
            customer_prefers_replacement_if_high: false,
            estimated_price: 159,
            final_price: 179,
            diagnostic_fee: 20,
            status: 'Picked Up / Closed',
            priority: 'normal',
            intake_staff: null,
            assigned_technician: null,
            intake_date: new Date().toISOString(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            history: [],
            notes: [],
            repair_actions: [
                {
                    id: 1,
                    ticket_id: 14,
                    repair_category_id: 1,
                    repair_category_name: 'Screen Repair',
                    action_description: 'Replaced cracked screen assembly',
                    part_cost: 50,
                    labor_minutes: 30,
                    difficulty_level: 2,
                    risk_level: 1,
                    calculated_price: 179,
                    final_price: 179,
                    status: 'completed',
                    performed_by: 'Alex',
                    performed_at: new Date().toISOString(),
                    requires_soldering: false,
                },
            ],
        });

        render(
            <MemoryRouter initialEntries={['/tickets/14/invoice']}>
                <Routes>
                    <Route path="/tickets/:ticketId/invoice" element={<InvoicePrintPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByText('Invoice')).toBeInTheDocument();
        expect(screen.getByText('TR-00014')).toBeInTheDocument();
        expect(screen.getByText('Invoice Customer')).toBeInTheDocument();
        expect(screen.getByText('Final total')).toBeInTheDocument();
        expect(screen.getAllByText(/\$179\.00/)).toHaveLength(2);

        await waitFor(() => {
            expect(fetchTicket).toHaveBeenCalledWith('14');
        });
    });
});
