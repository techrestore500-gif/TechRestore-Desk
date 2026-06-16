import { render, screen, waitFor, within } from '@testing-library/react';
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

    it('counts only picked up unpaid jobs in the unpaid summary and balance column', async () => {
        vi.mocked(fetchTickets).mockResolvedValue([
            {
                id: 11,
                ticket_number: 'TR-00011',
                customer_id: 10,
                customer_name: 'Closed Unpaid',
                customer_phone: '555-1000',
                device_label: 'Pixel 7',
                issue_category: 'Screen',
                status: 'Picked Up / Closed',
                payment_status: 'unpaid',
                intake_date: new Date().toISOString(),
                estimated_price: 25,
                final_price: 25,
                updated_at: new Date().toISOString(),
            },
            {
                id: 12,
                ticket_number: 'TR-00012',
                customer_id: 11,
                customer_name: 'Open Unpaid',
                customer_phone: '555-2000',
                device_label: 'iPhone 13',
                issue_category: 'Battery',
                status: 'In Repair',
                payment_status: 'unpaid',
                intake_date: new Date().toISOString(),
                estimated_price: 50,
                final_price: 50,
                updated_at: new Date().toISOString(),
            },
            {
                id: 13,
                ticket_number: 'TR-00013',
                customer_id: 12,
                customer_name: 'Closed Paid',
                customer_phone: '555-3000',
                device_label: 'Galaxy S22',
                issue_category: 'Port',
                status: 'Picked Up / Closed',
                payment_status: 'paid',
                intake_date: new Date().toISOString(),
                estimated_price: 40,
                final_price: 40,
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

        const unpaidTile = await screen.findByText('Unpaid');
        expect(unpaidTile.parentElement).not.toBeNull();
        await screen.findByText('TR-00011');
        expect(unpaidTile.parentElement as HTMLElement).toHaveTextContent('1');

        const unpaidRow = (await screen.findByText('TR-00011')).closest('tr');
        expect(unpaidRow).not.toBeNull();
        expect(within(unpaidRow as HTMLElement).getByText('$25.00')).toBeInTheDocument();

        const openRow = (await screen.findByText('TR-00012')).closest('tr');
        expect(openRow).not.toBeNull();
        expect(within(openRow as HTMLElement).getByText('Paid')).toBeInTheDocument();
    });
});
