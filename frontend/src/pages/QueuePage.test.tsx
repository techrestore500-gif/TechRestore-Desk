import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { assignQueueTicket, fetchTechnicianQueue } from '../api/tickets';
import { QueryTestProvider } from '../test/queryTestUtils';
import { QueuePage } from './QueuePage';

vi.mock('../api/tickets', () => ({
    fetchTechnicianQueue: vi.fn(),
    assignQueueTicket: vi.fn(),
}));

describe('QueuePage', () => {
    it('loads queue sections and supports refresh', async () => {
        vi.mocked(fetchTechnicianQueue).mockResolvedValue({
            'Loaner Outstanding': [
                {
                    id: 88,
                    ticket_number: 'TR-00088',
                    customer_id: 4,
                    customer_name: 'Queue Customer',
                    customer_phone: '555-2222',
                    manufacturer: 'Apple',
                    model_name: 'iPhone XR',
                    issue_category: 'Battery',
                    status: 'Loaner Outstanding',
                    customer_approval_limit: null,
                    assigned_technician: 'Pat',
                    intake_date: new Date().toISOString(),
                    created_at: new Date().toISOString(),
                },
            ],
            'Waiting for Parts': [],
            'Customer Approval Needed': [],
            'New Intake': [],
            'Needs Diagnosis': [],
        });
        vi.mocked(assignQueueTicket).mockResolvedValue({
            ticket_id: 88,
            assigned_technician: 'Pat',
            updated: true,
        });

        render(
            <QueryTestProvider>
                <MemoryRouter>
                    <QueuePage />
                </MemoryRouter>
            </QueryTestProvider>
        );

        expect(await screen.findByText('TR-00088')).toBeInTheDocument();
        expect(screen.getByText('Queue Customer · 555-2222')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: '↺ Refresh' }));

        await waitFor(() => {
            expect(fetchTechnicianQueue).toHaveBeenCalledTimes(2);
        });
    });
});
