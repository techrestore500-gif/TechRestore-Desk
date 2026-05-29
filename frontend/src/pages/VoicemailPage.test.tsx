import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { deleteVoicemail, fetchVoicemailAudio, fetchVoicemails, updateVoicemail } from '../api/system';
import VoicemailPage from './VoicemailPage';

vi.mock('../api/system', () => ({
    fetchVoicemails: vi.fn(),
    fetchVoicemailAudio: vi.fn(),
    updateVoicemail: vi.fn(),
    deleteVoicemail: vi.fn(),
}));

// jsdom does not implement URL.createObjectURL / revokeObjectURL.
// Define them so the blob-URL audio loading path can be tested.
beforeEach(() => {
    URL.createObjectURL = vi.fn(() => 'blob:http://localhost/fake-audio-uuid');
    URL.revokeObjectURL = vi.fn();
});

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
        // fetchVoicemailAudio is called automatically for voicemails with a recording_url.
        // Return a minimal valid audio blob so the <audio> element gets a src blob URL.
        const fakeAudioBlob = new Blob(['fake-audio'], { type: 'audio/mpeg' });
        vi.mocked(fetchVoicemailAudio).mockResolvedValue({ blob: fakeAudioBlob, contentType: 'audio/mpeg' });
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

        // Audio is loaded via fetchVoicemailAudio (which injects the Bearer token), then
        // served to the <audio> element as a blob URL — not a direct backend path.
        await waitFor(() => {
            expect(fetchVoicemailAudio).toHaveBeenCalledWith(7);
        });
        const audio = await waitFor(() => {
            const el = document.querySelector('audio');
            // Blob URL is set only after fetchVoicemailAudio resolves and createObjectURL runs.
            if (!el?.getAttribute('src')) throw new Error('blob URL not set yet');
            return el;
        });
        expect(audio?.getAttribute('src')).toBe('blob:http://localhost/fake-audio-uuid');

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

    it('shows retry button when audio fails to load', async () => {
        vi.mocked(fetchVoicemails).mockResolvedValue([
            {
                id: 8,
                caller_number: '+15555550222',
                called_number: '+15555550123',
                call_sid: 'CA888',
                recording_sid: 'RE888',
                recording_url: 'https://api.twilio.com/recordings/RE888',
                recording_duration_seconds: 21,
                transcription_text: null,
                notes: null,
                status: 'new',
                customer_id: null,
                customer_name: null,
                customer_phone: null,
                ticket_id: null,
                listened_at: null,
                archived_at: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        ]);
        vi.mocked(fetchVoicemailAudio).mockRejectedValue(
            new Error('Recording is not ready yet. Try again in a few seconds.')
        );

        render(
            <MemoryRouter>
                <VoicemailPage />
            </MemoryRouter>
        );

        expect(await screen.findByText('Voicemail Inbox')).toBeInTheDocument();
        expect(await screen.findByText('Recording is not ready yet. Try again in a few seconds.')).toBeInTheDocument();
        expect(await screen.findByRole('button', { name: 'Retry' })).toBeInTheDocument();
    });
});
