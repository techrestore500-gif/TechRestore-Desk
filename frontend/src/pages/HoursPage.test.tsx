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
                work_date: '2026-05-10',
                hours_worked: 2.5,
                work_description: 'Battery replacement',
                created_at: '2026-05-10T10:00:00Z',
                updated_at: '2026-05-10T10:00:00Z',
            },
        ]);
        vi.mocked(fetchHoursSummary).mockResolvedValue({
            by_technician: { Mattis: 2.5 },
            total_hours: 2.5,
            date_range: { start: 'all', end: 'all' },
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
            expect(fetchHours).toHaveBeenCalledTimes(1);
        });

        expect(screen.getAllByDisplayValue('Mattis')).toHaveLength(2);
        expect(screen.getByText('Total: 2:30')).toBeInTheDocument();

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
