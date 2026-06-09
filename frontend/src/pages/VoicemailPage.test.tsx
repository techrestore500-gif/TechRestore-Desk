import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { deleteVoicemail, fetchVoicemailAudio, fetchVoicemails, updateVoicemail } from "../api/system";
import VoicemailPage from "./VoicemailPage";

vi.mock("../api/system", () => ({
    fetchVoicemails: vi.fn(),
    fetchVoicemailAudio: vi.fn(),
    updateVoicemail: vi.fn(),
    deleteVoicemail: vi.fn(),
}));

beforeEach(() => {
    URL.createObjectURL = vi.fn(() => "blob:http://localhost/fake-audio-uuid");
    URL.revokeObjectURL = vi.fn();
    HTMLMediaElement.prototype.play = vi.fn().mockResolvedValue(undefined);
});

describe("VoicemailPage", () => {
    it("renders compact row, opens vertical ellipsis menu, and supports actions", async () => {
        vi.mocked(fetchVoicemails).mockResolvedValue([
            {
                id: 7,
                caller_number: "+15555550111",
                called_number: "+18772683048",
                call_sid: "CA123",
                recording_sid: "RE123",
                recording_url: "https://api.twilio.com/recordings/RE123",
                recording_duration_seconds: 34,
                transcription_text: "Please call me back.",
                notes: "Left after hours",
                status: "new",
                customer_id: 3,
                customer_name: "Alex Customer",
                customer_phone: "+15555550111",
                ticket_id: null,
                listened_at: null,
                archived_at: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        ]);
        vi.mocked(updateVoicemail).mockResolvedValue({
            id: 7,
            caller_number: "+15555550111",
            called_number: "+18772683048",
            call_sid: "CA123",
            recording_sid: "RE123",
            recording_url: "https://api.twilio.com/recordings/RE123",
            recording_duration_seconds: 34,
            transcription_text: "Please call me back.",
            notes: "Left after hours",
            status: "listened",
            customer_id: 3,
            customer_name: "Alex Customer",
            customer_phone: "+15555550111",
            ticket_id: null,
            listened_at: new Date().toISOString(),
            archived_at: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
        });
        vi.mocked(deleteVoicemail).mockResolvedValue();
        vi.mocked(fetchVoicemailAudio).mockResolvedValue({
            blob: new Blob(["fake-audio"], { type: "audio/mpeg" }),
            contentType: "audio/mpeg",
        });
        vi.spyOn(window, "confirm").mockReturnValue(true);

        render(
            <MemoryRouter>
                <VoicemailPage />
            </MemoryRouter>
        );

        expect(await screen.findByText("Voicemail Inbox")).toBeInTheDocument();
        expect(await screen.findByText("From: +1 555-555-0111")).toBeInTheDocument();
        expect(await screen.findByText(/Line: \+1 877-268-3048/)).toBeInTheDocument();
        expect(await screen.findByText(/0:34/)).toBeInTheDocument();
        expect(await screen.findByRole("button", { name: "Play" })).toBeInTheDocument();

        const menuButton = await screen.findByRole("button", { name: "More actions for voicemail 7" });
        expect(menuButton).toBeInTheDocument();
        expect(menuButton.textContent).toBe("⋮");

        fireEvent.click(menuButton);
        expect(await screen.findByRole("menuitem", { name: "Mark listened" })).toBeInTheDocument();
        expect(await screen.findByRole("menuitem", { name: "Mark done" })).toBeInTheDocument();
        expect(await screen.findByRole("menuitem", { name: "Add/Edit note" })).toBeInTheDocument();
        expect(await screen.findByRole("menuitem", { name: "Copy caller number" })).toBeInTheDocument();
        expect(await screen.findByRole("menuitem", { name: "Delete" })).toBeInTheDocument();

        fireEvent.click(screen.getByRole("menuitem", { name: "Add/Edit note" }));
        fireEvent.change(await screen.findByPlaceholderText("Add follow-up note"), {
            target: { value: "Call after lunch" },
        });
        fireEvent.click(screen.getByRole("button", { name: "Save note" }));
        await waitFor(() => {
            expect(updateVoicemail).toHaveBeenCalledWith(7, { note: "Call after lunch" });
        });

        fireEvent.click(screen.getByRole("button", { name: "Play" }));
        await waitFor(() => {
            expect(fetchVoicemailAudio).toHaveBeenCalledWith(7);
        });

        const audio = await waitFor(() => {
            const element = document.querySelector("audio");
            if (!element) throw new Error("audio not ready");
            return element;
        });
        fireEvent.play(audio as HTMLAudioElement);
        await waitFor(() => {
            expect(updateVoicemail).toHaveBeenCalledWith(7, { status: "listened" });
        });

        fireEvent.click(screen.getByRole("button", { name: "More actions for voicemail 7" }));
        fireEvent.click(screen.getByRole("menuitem", { name: "Mark done" }));
        await waitFor(() => {
            expect(updateVoicemail).toHaveBeenCalledWith(7, { status: "archived" });
        });

        fireEvent.click(screen.getByRole("button", { name: "More actions for voicemail 7" }));
        fireEvent.click(screen.getByRole("menuitem", { name: "Delete" }));
        await waitFor(() => {
            expect(deleteVoicemail).toHaveBeenCalledWith(7);
        });
    });

    it("shows unknown fallbacks and disables copy caller number when missing", async () => {
        vi.mocked(fetchVoicemails).mockResolvedValue([
            {
                id: 8,
                caller_number: null,
                called_number: null,
                call_sid: "CA888",
                recording_sid: "RE888",
                recording_url: "https://api.twilio.com/recordings/RE888",
                recording_duration_seconds: 21,
                transcription_text: null,
                notes: null,
                status: "new",
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
        vi.mocked(fetchVoicemailAudio).mockRejectedValue(new Error("Recording is not ready yet. Try again in a few seconds."));

        render(
            <MemoryRouter>
                <VoicemailPage />
            </MemoryRouter>
        );

        expect(await screen.findByText("From: Unknown")).toBeInTheDocument();
        expect(await screen.findByText(/Line: Unknown/)).toBeInTheDocument();

        fireEvent.click(await screen.findByRole("button", { name: "More actions for voicemail 8" }));
        const copyButton = await screen.findByRole("menuitem", { name: "Copy caller number" });
        expect(copyButton).toBeDisabled();
    });
});
