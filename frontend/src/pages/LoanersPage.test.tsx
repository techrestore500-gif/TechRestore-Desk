import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import LoanersPage from './LoanersPage';
import { fetchLoaners, updateLoanerStatus } from '../api/tickets';

vi.mock('../api/tickets', () => ({
    fetchLoaners: vi.fn(),
    createLoaner: vi.fn(),
    checkoutLoaner: vi.fn(),
    returnLoaner: vi.fn(),
    updateLoanerStatus: vi.fn(),
}));

describe('LoanersPage', () => {
    it('loads loaners and refreshes after quick status update', async () => {
        vi.mocked(fetchLoaners).mockResolvedValue([
            {
                id: 7,
                loaner_code: 'LN-007',
                manufacturer: 'Samsung',
                model: 'Galaxy S21',
                carrier_compatibility: null,
                charger_type: null,
                sim_type: null,
                filter_status: null,
                condition_current: 'Good',
                status: 'Available',
                default_deposit: 50,
                notes: null,
                active: true,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        ]);
        vi.mocked(updateLoanerStatus).mockResolvedValue({
            id: 7,
            loaner_code: 'LN-007',
            manufacturer: 'Samsung',
            model: 'Galaxy S21',
            carrier_compatibility: null,
            charger_type: null,
            sim_type: null,
            filter_status: null,
            condition_current: 'Good',
            status: 'Returned Needs Reset',
            default_deposit: 50,
            notes: null,
            active: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
        });

        render(
            <MemoryRouter>
                <LoanersPage />
            </MemoryRouter>
        );

        expect(await screen.findByText('LN-007')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Needs reset' }));

        await waitFor(() => {
            expect(updateLoanerStatus).toHaveBeenCalledWith(7, 'Returned Needs Reset');
        });

        await waitFor(() => {
            expect(fetchLoaners).toHaveBeenCalledTimes(2);
        });
    });
});
