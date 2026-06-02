import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
    clockIn,
    fetchActiveClockSession,
    fetchHours,
    fetchHoursSummary,
} from '../api/hours';
import { HoursPage } from './HoursPage';

vi.mock('../api/hours', () => ({
    clockIn: vi.fn(),
    clockOut: vi.fn(),
    fetchActiveClockSession: vi.fn(),
    fetchHours: vi.fn(),
    fetchHoursSummary: vi.fn(),
    logHours: vi.fn(),
}));

describe('HoursPage', () => {
    beforeEach(() => {
        const now = new Date();
        const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;

        const storage = new Map<string, string>();
        storage.set('techRestore.techRoster', JSON.stringify(['Mattis']));

        Object.defineProperty(window, 'localStorage', {
            configurable: true,
            value: {
                getItem: (key: string) => storage.get(key) ?? null,
                setItem: (key: string, value: string) => {
                    storage.set(key, value);
                },
            },
        });

        vi.mocked(fetchHours).mockResolvedValue([
            {
                id: 1,
                ticket_id: 12,
                technician: 'Mattis',
                work_date: today,
                hours_worked: 1.3333333333,
                work_description: 'Kyocera E4810 screen replacement bench work.',
                created_at: `${today}T10:00:00Z`,
                updated_at: `${today}T10:00:00Z`,
            },
            {
                id: 2,
                ticket_id: 12,
                technician: 'Mattis',
                work_date: '2026-06-01T00:00:00+00:00',
                hours_worked: 1.6666666667,
                work_description: 'Yesterday entry: Tech Restore queue follow-up and shop work.',
                created_at: '2026-06-01T10:00:00Z',
                updated_at: '2026-06-01T10:00:00Z',
            },
        ]);
        vi.mocked(fetchHoursSummary).mockResolvedValue({
            by_technician: { Mattis: 3.0 },
            total_hours: 3.0,
            date_range: { start: today.slice(0, 8) + '01', end: today },
        });
        vi.mocked(fetchActiveClockSession).mockResolvedValue(null);
        vi.mocked(clockIn).mockResolvedValue({
            id: 22,
            ticket_id: null,
            technician: 'Mattis',
            work_description: null,
            clocked_in_at: '2026-05-10T15:00:00Z',
            clocked_out_at: null,
            status: 'active',
            elapsed_seconds: 0,
            elapsed_hours: 0,
            created_at: '2026-05-10T15:00:00Z',
            updated_at: '2026-05-10T15:00:00Z',
        });
    });

    it('defaults to Mattis and allows clocking in', async () => {
        render(
            <MemoryRouter>
                <HoursPage />
            </MemoryRouter>
        );

        await waitFor(() => {
            expect(fetchHours).toHaveBeenCalled();
        });

        expect(screen.getAllByDisplayValue('Mattis')).toHaveLength(2);
        await waitFor(() => {
            expect(screen.getByText('Total: 1:20')).toBeInTheDocument();
        });

        expect(screen.queryByText(/Work date: 6\/1\/2026/)).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Clock In' }));

        await waitFor(() => {
            expect(clockIn).toHaveBeenCalledWith({
                technician: 'Mattis',
                ticket_id: undefined,
                work_description: undefined,
            });
        });

        expect(fetchActiveClockSession).toHaveBeenCalledWith('Mattis');
    });
});
