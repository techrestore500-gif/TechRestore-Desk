import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { fetchReportSummary } from '../api/tickets';
import ReportsPage from './ReportsPage';

vi.mock('../api/tickets', () => ({
    fetchReportSummary: vi.fn(),
}));

describe('ReportsPage', () => {
    it('loads and displays report metrics for the selected date range', async () => {
        vi.mocked(fetchReportSummary).mockResolvedValue({
            date_range: { start: '2026-05-10', end: '2026-05-10' },
            technician_filter: null,
            repair_category_filter: null,
            created_tickets_count: 3,
            closed_tickets_count: 2,
            total_revenue: 450,
            average_closed_ticket_revenue: 225,
            total_hours: 5,
            revenue_per_hour: 90,
            available_technicians: ['Jordan'],
            available_repair_categories: ['Screen Repair'],
            technician_breakdown: [
                {
                    technician: 'Jordan',
                    total_hours: 5,
                    tickets_worked: 2,
                    closed_tickets_count: 2,
                    total_revenue: 450,
                },
            ],
            repair_category_breakdown: [
                {
                    repair_category: 'Screen Repair',
                    action_count: 2,
                    ticket_count: 2,
                    total_final_price: 450,
                },
            ],
        });

        render(
            <MemoryRouter>
                <ReportsPage />
            </MemoryRouter>
        );

        await waitFor(() => {
            expect(fetchReportSummary).toHaveBeenCalledTimes(1);
        });

        expect(await screen.findAllByText('$450.00')).toHaveLength(2);
        expect(screen.getByText('Created tickets')).toBeInTheDocument();
        expect(screen.getByText('$90.00')).toBeInTheDocument();
        expect(screen.getByText('Technician breakdown')).toBeInTheDocument();
        expect(screen.getAllByText('Screen Repair')).toHaveLength(2);

        fireEvent.change(screen.getByLabelText('Start date'), {
            target: { value: '2026-05-09' },
        });
        fireEvent.change(screen.getByLabelText('Technician'), {
            target: { value: 'Jordan' },
        });
        fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }));

        await waitFor(() => {
            expect(fetchReportSummary).toHaveBeenCalledTimes(2);
        });

        const secondCall = vi.mocked(fetchReportSummary).mock.calls[1][0];
        expect(secondCall).toBeDefined();
        if (!secondCall) {
            throw new Error('Expected second fetchReportSummary call args');
        }
        expect(secondCall).toEqual({
            startDate: '2026-05-09',
            endDate: expect.any(String),
            technician: 'Jordan',
            repairCategory: undefined,
        });
        expect(secondCall.endDate).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    });
});
