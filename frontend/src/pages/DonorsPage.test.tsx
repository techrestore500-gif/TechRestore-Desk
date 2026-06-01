import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { DonorsPage } from './DonorsPage';
import {
    fetchDonors,
    fetchParts,
    updateDonor,
} from '../api/inventory';

vi.mock('../api/inventory', () => ({
    fetchDonors: vi.fn(),
    fetchParts: vi.fn(),
    createDonor: vi.fn(),
    harvestPartFromDonor: vi.fn(),
    updateDonor: vi.fn(),
}));

describe('DonorsPage', () => {
    it('loads donors and refreshes after adding an available part', async () => {
        vi.mocked(fetchDonors).mockResolvedValue([
            {
                id: 1,
                device_identifier: 'DON-001',
                device_model: 'Galaxy S22',
                status: 'Available for Parts',
                condition_notes: 'Back glass cracked',
                parts_harvested: [],
                parts_available: [],
                acquisition_date: '2026-05-01',
                retirement_date: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        ]);

        vi.mocked(fetchParts).mockResolvedValue([
            {
                id: 11,
                part_number: 'SCR-11',
                part_name: 'Screen',
                category: 'Display',
                device_compatibility: null,
                supplier: null,
                cost: 20,
                retail_price: 60,
                status: 'In Stock',
                quantity_on_hand: 3,
                quantity_ordered: 0,
                reorder_level: 1,
                reorder_quantity: 2,
                notes: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        ]);

        vi.mocked(updateDonor).mockResolvedValue({
            id: 1,
            device_identifier: 'DON-001',
            device_model: 'Galaxy S22',
            status: 'Available for Parts',
            condition_notes: 'Back glass cracked',
            parts_harvested: [],
            parts_available: [11],
            acquisition_date: '2026-05-01',
            retirement_date: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
        });

        render(<DonorsPage />);

        expect(await screen.findByText('DON-001')).toBeInTheDocument();

        fireEvent.change(screen.getAllByRole('combobox')[0], {
            target: { value: '11' },
        });
        fireEvent.click(screen.getByRole('button', { name: 'Add Available Part' }));

        await waitFor(() => {
            expect(updateDonor).toHaveBeenCalledWith(1, { parts_available: [11] });
        });

        await waitFor(() => {
            expect(fetchDonors).toHaveBeenCalledTimes(2);
            expect(fetchParts).toHaveBeenCalledTimes(2);
        });
    });
});
