import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import TicketsPage from './TicketsPage';
import { fetchTickets } from '../api/tickets';
import { QueryTestProvider } from '../test/queryTestUtils';

vi.mock('../api/tickets', () => ({
    fetchTickets: vi.fn(),
}));

describe('TicketsPage', () => {
    it('loads and renders ticket cards', async () => {
        vi.mocked(fetchTickets).mockResolvedValue([
            {
                id: 1,
                ticket_number: 'TR-00001',
                customer_id: 10,
                customer_name: 'Test Customer',
                customer_phone: '555-1111',
                device_label: 'iPhone 11',
                issue_category: 'Screen',
                status: 'New Intake',
                payment_status: 'unpaid',
                intake_date: new Date().toISOString(),
                estimated_price: null,
                final_price: null,
                updated_at: new Date().toISOString(),
            },
        ]);

        render(
            <QueryTestProvider>
                <MemoryRouter>
                    <TicketsPage />
                </MemoryRouter>
            </QueryTestProvider>
        );

        expect(screen.getByText('Loading tickets…')).toBeInTheDocument();

        await waitFor(() => {
            expect(fetchTickets).toHaveBeenCalledWith('');
        });

        expect(await screen.findByText('TR-00001')).toBeInTheDocument();
        expect(screen.getByText('Test Customer')).toBeInTheDocument();
        expect(screen.getByText('Screen')).toBeInTheDocument();
    });
});
