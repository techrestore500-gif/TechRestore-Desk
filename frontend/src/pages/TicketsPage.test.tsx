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
    it('loads and renders ticket rows', async () => {
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
                completed_at: null,
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

    it('shows correct payment states without defaulting to Paid', async () => {
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
                completed_at: null,
                estimated_price: 25,
                final_price: 25,
                updated_at: new Date().toISOString(),
            },
            {
                id: 12,
                ticket_number: 'TR-00012',
                customer_id: 11,
                customer_name: 'Open TBD',
                customer_phone: '555-2000',
                device_label: 'iPhone 13',
                issue_category: 'Battery',
                status: 'In Repair',
                payment_status: 'unpaid',
                intake_date: new Date().toISOString(),
                completed_at: null,
                estimated_price: null,
                final_price: null,
                updated_at: new Date().toISOString(),
            },
            {
                id: 13,
                ticket_number: 'TR-00013',
                customer_id: 12,
                customer_name: 'Declined No Charge',
                customer_phone: '555-3000',
                device_label: 'Galaxy S22',
                issue_category: 'Port',
                status: 'Customer Declined',
                payment_status: 'paid',
                intake_date: new Date().toISOString(),
                completed_at: null,
                estimated_price: 0,
                final_price: 0,
                updated_at: new Date().toISOString(),
            },
            {
                id: 14,
                ticket_number: 'TR-00014',
                customer_id: 13,
                customer_name: 'Needs Final',
                customer_phone: '555-4000',
                device_label: 'MacBook Pro',
                issue_category: 'Board',
                status: 'Picked Up / Closed',
                payment_status: 'unpaid',
                intake_date: new Date().toISOString(),
                completed_at: null,
                estimated_price: null,
                final_price: null,
                updated_at: new Date().toISOString(),
            },
            {
                id: 15,
                ticket_number: 'TR-00015',
                customer_id: 14,
                customer_name: 'Already Paid',
                customer_phone: '555-5000',
                device_label: 'iPad',
                issue_category: 'Screen',
                status: 'Picked Up / Closed',
                payment_status: 'paid',
                intake_date: new Date().toISOString(),
                completed_at: null,
                estimated_price: 40,
                final_price: 40,
                updated_at: new Date().toISOString(),
            },
            {
                id: 16,
                ticket_number: 'TR-00016',
                customer_id: 15,
                customer_name: 'Mystery Payment',
                customer_phone: '555-6000',
                device_label: 'Canon Canon SX740',
                issue_category: 'Display',
                status: 'In Repair',
                payment_status: 'pending' as unknown as 'paid',
                intake_date: new Date().toISOString(),
                completed_at: null,
                estimated_price: 20,
                final_price: 20,
                updated_at: new Date().toISOString(),
            },
            {
                id: 18,
                ticket_number: 'TR-00018',
                customer_id: 17,
                customer_name: 'Raizy Krieger',
                customer_phone: '732-732-2743',
                device_label: 'Canon SX740',
                issue_category: 'Display issue',
                status: 'Ready for Pickup',
                payment_status: 'unpaid',
                intake_date: new Date().toISOString(),
                completed_at: null,
                estimated_price: 75,
                final_price: 75,
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
        await screen.findByText('TR-00018');
        expect(unpaidTile.parentElement as HTMLElement).toHaveTextContent('2');

        const unpaidRow = (await screen.findByText('TR-00011')).closest('tr');
        expect(unpaidRow).not.toBeNull();
        expect(within(unpaidRow as HTMLElement).getByText('Unpaid $25.00')).toBeInTheDocument();

        const tbdRow = (await screen.findByText('TR-00012')).closest('tr');
        expect(tbdRow).not.toBeNull();
        expect(within(tbdRow as HTMLElement).getByText('TBD')).toBeInTheDocument();

        const noChargeRow = (await screen.findByText('TR-00013')).closest('tr');
        expect(noChargeRow).not.toBeNull();
        expect(within(noChargeRow as HTMLElement).getByText('No charge')).toBeInTheDocument();

        const needsFinalRow = (await screen.findByText('TR-00014')).closest('tr');
        expect(needsFinalRow).not.toBeNull();
        expect(within(needsFinalRow as HTMLElement).getByText('Needs final')).toBeInTheDocument();

        const paidRow = (await screen.findByText('TR-00015')).closest('tr');
        expect(paidRow).not.toBeNull();
        expect(within(paidRow as HTMLElement).getByText('Paid')).toBeInTheDocument();

        const unknownRow = (await screen.findByText('TR-00016')).closest('tr');
        expect(unknownRow).not.toBeNull();
        expect(within(unknownRow as HTMLElement).getByText('Unknown')).toBeInTheDocument();
        expect(within(unknownRow as HTMLElement).getByText('Canon SX740')).toBeInTheDocument();

        const raizyRow = (await screen.findByText('TR-00018')).closest('tr');
        expect(raizyRow).not.toBeNull();
        expect(within(raizyRow as HTMLElement).getByText('Raizy Krieger')).toBeInTheDocument();
        expect(within(raizyRow as HTMLElement).getByText('Display issue')).toBeInTheDocument();
        expect(within(raizyRow as HTMLElement).getByText('Ready for Pickup')).toBeInTheDocument();
        expect(within(raizyRow as HTMLElement).getByText('Unpaid $75.00')).toBeInTheDocument();
    });

    it('shows the zaks ticket as unpaid $20', async () => {
        vi.mocked(fetchTickets).mockResolvedValue([
            {
                id: 17,
                ticket_number: 'TR-00017',
                customer_id: 16,
                customer_name: 'zaks',
                customer_phone: '347-243-4830',
                device_label: 'canon Canon SX740',
                issue_category: 'Display not turning on',
                status: 'Completed',
                payment_status: 'unpaid',
                intake_date: new Date().toISOString(),
                completed_at: null,
                estimated_price: 20,
                final_price: 20,
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

        const zaksRow = (await screen.findByText('TR-00017')).closest('tr');
        expect(zaksRow).not.toBeNull();
        expect(within(zaksRow as HTMLElement).getByText('Zaks')).toBeInTheDocument();
        expect(within(zaksRow as HTMLElement).getByText('Canon SX740')).toBeInTheDocument();
        expect(within(zaksRow as HTMLElement).getByText('Unpaid $20.00')).toBeInTheDocument();
    });
});
