import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { deleteVoicemail, fetchVoicemails, updateVoicemail } from '../api/system';
import VoicemailPage from './VoicemailPage';

vi.mock('../api/system', () => ({
    fetchVoicemails: vi.fn(),
    updateVoicemail: vi.fn(),
    deleteVoicemail: vi.fn(),
}));

describe('VoicemailPage', () => {
    it('renders voicemail records and quick actions', async () => {
        vi.mocked(fetchVoicemails).mockResolvedValue([
            {
                id: 7,
                caller_number: '+15555550111',
                called_number: '+15555550123',
                call_sid: 'CA123',
                recording_sid: 'RE123',
                recording_url: 'https://api.twilio.com/recordings/RE123',
                recording_duration_seconds: 34,
                transcription_text: 'Please call me back.',
                notes: 'Left after hours',
                status: 'new',
                customer_id: 3,
                customer_name: 'Alex Customer',
                customer_phone: '+15555550111',
                ticket_id: null,
                listened_at: null,
                archived_at: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        ]);
        vi.mocked(updateVoicemail).mockResolvedValue({
            id: 7,
            caller_number: '+15555550111',
            called_number: '+15555550123',
            call_sid: 'CA123',
            recording_sid: 'RE123',
            recording_url: 'https://api.twilio.com/recordings/RE123',
            recording_duration_seconds: 34,
            transcription_text: 'Please call me back.',
            notes: 'Left after hours',
            status: 'listened',
            customer_id: 3,
            customer_name: 'Alex Customer',
            customer_phone: '+15555550111',
            ticket_id: null,
            listened_at: new Date().toISOString(),
            archived_at: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
        });
        vi.mocked(deleteVoicemail).mockResolvedValue();
        vi.spyOn(window, 'confirm').mockReturnValue(true);

        render(
            <MemoryRouter>
                <VoicemailPage />
            </MemoryRouter>
        );

        expect(await screen.findByText('Voicemail Inbox')).toBeInTheDocument();
        expect(await screen.findByText('+15555550111')).toBeInTheDocument();
        expect(await screen.findByText('New')).toBeInTheDocument();
        expect(await screen.findByText(/Duration:/)).toBeInTheDocument();
        expect(await screen.findByText('Note added')).toBeInTheDocument();
        expect(await screen.findByRole('button', { name: 'Copy number' })).toBeInTheDocument();
        expect(await screen.findByRole('button', { name: 'Mark listened' })).toBeInTheDocument();
        expect(await screen.findByRole('button', { name: 'Mark done' })).toBeInTheDocument();
        expect(await screen.findByRole('button', { name: 'Delete' })).toBeInTheDocument();
        const audio = document.querySelector('audio');
        expect(audio).not.toBeNull();
        expect(audio?.getAttribute('src')).toBe('/api/voicemails/7/audio');

        fireEvent.play(audio as HTMLAudioElement);
        await waitFor(() => {
            expect(updateVoicemail).toHaveBeenCalledWith(7, { status: 'listened' });
        });

        fireEvent.click(screen.getByRole('button', { name: 'Mark listened' }));
        await waitFor(() => {
            expect(updateVoicemail).toHaveBeenCalledWith(7, { status: 'listened' });
        });

        fireEvent.click(screen.getByRole('button', { name: 'Mark done' }));
        await waitFor(() => {
            expect(updateVoicemail).toHaveBeenCalledWith(7, { status: 'archived' });
        });

        fireEvent.change(screen.getByPlaceholderText('Add follow-up note'), {
            target: { value: 'Call after lunch' },
        });
        fireEvent.click(screen.getByRole('button', { name: 'Add note' }));

        await waitFor(() => {
            expect(updateVoicemail).toHaveBeenCalledWith(7, { note: 'Call after lunch' });
        });

        fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
        await waitFor(() => {
            expect(deleteVoicemail).toHaveBeenCalledWith(7);
        });
    });
});
